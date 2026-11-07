#!/usr/bin/env python3
"""Stage MT7603 per-BSS steering ready after a checked MBSS open.

This is a focused, nonproduction successor to the hash-verified v14 tree.
The checked close/down publication and its race fixtures are separate work.
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
        raise ValueError(f"{label}: expected one source anchor, found {data.count(old)}")
    return data.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(), args.output.resolve()
    if not source.is_dir() or output.exists() or source in output.parents:
        parser.error("source must exist and output must be new and separate")
    manifest_path = source.parent / (source.name + "-composition.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("production_installed") is not False or not manifest.get("mbss_open_claim_composed"):
        parser.error("expected nonproduction claimed-open composition")
    records = {r["path"]: r for r in manifest["files"]}
    if len(records) != len(manifest["files"]):
        parser.error("duplicate source paths")
    files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if files != set(records):
        parser.error("source file set differs from manifest")
    for name, record in records.items():
        if digest((source / name).read_bytes()) != record["sha256"]:
            parser.error("source hash mismatch: " + name)

    core_name = "ap/ap_mbss.c"
    admission_name = "include/wr-iot-mbss-open-admission.inc"
    core = (source / core_name).read_bytes()
    core = one(core,
        b"if(pAd->ApCfg.BandSteering)\n\t\t{\n\t\t\tPBND_STRG_CLI_TABLE table;",
        b"if((!IS_MT7603(pAd) || pAd->ApCfg.BssidNum < 3 ||\n"
        b"    (BssId != 1 && BssId != 2)) && pAd->ApCfg.BandSteering)\n"
        b"\t\t{\n\t\t\tPBND_STRG_CLI_TABLE table;",
        core_name)
    helper = b"""#ifdef BAND_STEERING
/* The BSS_OPEN ticket remains live while the caller sends this status.
 * Non-MT7603 boards keep the original vendor MBSS_Open notification. */
VOID wr_iot_mbss_publish_ready(PRTMP_ADAPTER pAd, PNET_DEV pDev, INT BssId)
{
 PBND_STRG_CLI_TABLE table;
 if (!pAd || !pDev || !IS_MT7603(pAd) || !pAd->ApCfg.BandSteering ||
     BssId <= 0 || BssId >= pAd->ApCfg.BssidNum ||
     (UINT32)BssId >= sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]) ||
     pAd->ApCfg.MBSSID[BssId].wdev.if_dev != pDev)
  return;
 table = Get_BndStrgTable(pAd, BssId);
 if (table)
  BndStrg_SetInfFlags(pAd, &pAd->ApCfg.MBSSID[BssId].wdev, table, TRUE);
}
#endif

"""
    core = one(core, b"INT32 MBSS_Open(PNET_DEV pDev)\n{", helper + b"INT32 MBSS_Open(PNET_DEV pDev)\n{", core_name)
    admission = (source / admission_name).read_bytes()
    admission = one(admission,
        b"INT MBSS_VirtualIF_Open(PNET_DEV pDev)\n{",
        b"#ifdef BAND_STEERING\nVOID wr_iot_mbss_publish_ready(PRTMP_ADAPTER pAd, PNET_DEV pDev, INT BssId);\n#endif\nINT MBSS_VirtualIF_Open(PNET_DEV pDev)\n{",
        admission_name)
    admission = one(admission,
        b"int admitted,ret,observe_iot,bss_id=0,observed_bss=0;",
        b"int admitted,ret,observe_iot,bss_id=0,observed_bss=0,publish_ready=0;",
        admission_name)
    admission = one(admission,
        b"  if(wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,1))\n"
        b"   wr_iot_bss_open_finish_observed(&adapter->wr_iot_transition,\n"
        b"    adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,pDev,\n"
        b"    VIRTUAL_IF_NUM(adapter),&ticket,observed_bss);",
        b"  if(wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,1)){\n"
        b"   /* No competing lifecycle transition can retire this BSS_OPEN ticket.\n"
        b"    * Send the per-BSS ready event outside the IRQ lock, then retire. */\n"
        b"   publish_ready=IS_MT7603(adapter)&&observed_bss&&bss_id>0&&\n"
        b"    wr_iot_registry_count_matches(adapter->wr_iot_interface_refs,\n"
        b"     WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(adapter))&&\n"
        b"    adapter->wr_iot_transition.busy==WR_RADIO_BSS_OPEN&&\n"
        b"    adapter->wr_iot_transition.serial==ticket.serial;\n"
        b"   if(publish_ready){\n"
        b"    RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"#ifdef BAND_STEERING\n"
        b"    wr_iot_mbss_publish_ready(adapter,pDev,bss_id);\n"
        b"#endif\n"
        b"    RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"   }\n"
        b"   wr_iot_bss_open_finish_observed(&adapter->wr_iot_transition,\n"
        b"    adapter->wr_iot_interface_refs,WDEV_NUM_MAX+1,pDev,\n"
        b"    VIRTUAL_IF_NUM(adapter),&ticket,observed_bss);\n"
        b"  }",
        admission_name)
    shutil.copytree(source, output)
    (output / core_name).write_bytes(core)
    (output / admission_name).write_bytes(admission)
    for name, record in records.items():
        record["sha256"] = digest((output / name).read_bytes())
        if name in (core_name, admission_name):
            record["stage"] = record.get("stage", "driver") + "+mbss-steering-ready"
    manifest["files"] = list(records.values())
    manifest["mbss_steering_ready_staged"] = True
    manifest["mbss_steering_down_staged"] = False
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Staged {len(records)} checked files: {output}")
    print("Checked down publication and failure/race verification remain open")


if __name__ == "__main__":
    main()
