#!/usr/bin/env python3
"""Stage MT7603 per-BSS steering down after checked MBSS virtual DOWN.

Requires the hash-verified v15b ready candidate. This remains nonproduction.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def one(data: bytes, old: bytes, new: bytes, label: str) -> bytes:
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    old, new = old.replace(b"\n", nl), new.replace(b"\n", nl)
    if data.count(old) != 1:
        raise ValueError(f"{label}: expected one anchor, found {data.count(old)}")
    return data.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_dir() or output.exists() or source in output.parents:
        parser.error("source must exist and output must be new and separate")
    manifest = json.loads((source.parent / (source.name + "-composition.json")).read_text(encoding="utf-8"))
    if (manifest.get("production_installed") is not False or
            manifest.get("mbss_steering_ready_staged") is not True or
            manifest.get("mbss_steering_down_staged") is not False):
        parser.error("expected nonproduction v15b ready candidate")
    records = {record["path"]: record for record in manifest["files"]}
    files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if len(records) != len(manifest["files"]) or files != set(records):
        parser.error("source file set or manifest is ambiguous")
    for name, record in records.items():
        if digest((source / name).read_bytes()) != record["sha256"]:
            parser.error("source hash mismatch: " + name)

    core_name = "ap/ap_mbss.c"
    executor_name = "include/wr-iot-mbss-close-checked.inc"
    core = (source / core_name).read_bytes()
    core = one(core,
        b"if(pAd->ApCfg.BandSteering)\n\t{\n\t\tPBND_STRG_CLI_TABLE table;",
        b"if((!IS_MT7603(pAd) || pAd->ApCfg.BssidNum < 3 ||\n"
        b"    (BssId != 1 && BssId != 2)) && pAd->ApCfg.BandSteering)\n"
        b"\t{\n\t\tPBND_STRG_CLI_TABLE table;",
        core_name)
    helper = b"""/* The checked close owner still holds its CLOSE/BSS_CLOSE ticket here.
 * The old vendor MBSS_Close notification remains for other boards/BSS. */
VOID wr_iot_mbss_publish_down(PRTMP_ADAPTER pAd, PNET_DEV pDev, INT BssId)
{
 PBND_STRG_CLI_TABLE table;
 if (!pAd || !pDev || !IS_MT7603(pAd) || !pAd->ApCfg.BandSteering ||
     pAd->ApCfg.BssidNum < 3 || (BssId != 1 && BssId != 2) ||
     BssId >= pAd->ApCfg.BssidNum ||
     (UINT32)BssId >= sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]) ||
     pAd->ApCfg.MBSSID[BssId].wdev.if_dev != pDev)
  return;
 table = Get_BndStrgTable(pAd, BssId);
 if (table)
  BndStrg_SetInfFlags(pAd, &pAd->ApCfg.MBSSID[BssId].wdev, table, FALSE);
}
"""
    core = one(core,
        b"}\n#endif\n\nINT32 MBSS_Open(PNET_DEV pDev)",
        b"}\n" + helper + b"#endif\n\nINT32 MBSS_Open(PNET_DEV pDev)",
        core_name)

    executor = (source / executor_name).read_bytes()
    executor = one(executor,
        b"INT wr_iot_mbss_close_checked(PNET_DEV dev,unsigned long generation,",
        b"#if defined(MT_MAC) && defined(BAND_STEERING)\n"
        b"VOID wr_iot_mbss_publish_down(PRTMP_ADAPTER ad, PNET_DEV dev, INT bss_id);\n"
        b"#endif\nINT wr_iot_mbss_close_checked(PNET_DEV dev,unsigned long generation,",
        executor_name)
    executor = one(executor,
        b"ret=wr_iot_virtual_down_checked(ad,ticket);\n"
        b" if(ret!=NDIS_STATUS_SUCCESS)\n"
        b"  return wr_iot_mbss_close_fail(ad,r,dev,generation,token,ticket);\n"
        b" RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);",
        b"ret=wr_iot_virtual_down_checked(ad,ticket);\n"
        b" if(ret!=NDIS_STATUS_SUCCESS)\n"
        b"  return wr_iot_mbss_close_fail(ad,r,dev,generation,token,ticket);\n"
        b" /* Confirmed DOWN precedes per-BSS daemon status. The close ticket\n"
        b"  * excludes another radio lifecycle transition until retirement. */\n"
        b"#if defined(MT_MAC) && defined(BAND_STEERING)\n"
        b" wr_iot_mbss_publish_down(ad,dev,bss_id);\n"
        b"#endif\n"
        b" RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);",
        executor_name)
    shutil.copytree(source, output)
    (output / core_name).write_bytes(core)
    (output / executor_name).write_bytes(executor)
    for name, record in records.items():
        record["sha256"] = digest((output / name).read_bytes())
        if name in (core_name, executor_name):
            record["stage"] = record.get("stage", "driver") + "+mbss-steering-down"
    manifest["files"] = list(records.values())
    manifest["mbss_steering_down_staged"] = True
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Staged {len(records)} checked files: {output}")
    print("No target compile, failure/race fixture or device verification")


if __name__ == "__main__":
    main()
