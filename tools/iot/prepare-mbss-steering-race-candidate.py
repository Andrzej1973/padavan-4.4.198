#!/usr/bin/env python3
"""Stage MBSS steering intent recheck/compensation in an isolated tree."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def one(data: bytes, old: bytes, new: bytes) -> bytes:
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    old, new = old.replace(b"\n", nl), new.replace(b"\n", nl)
    if data.count(old) != 1:
        raise ValueError(f"expected one reviewed anchor, found {data.count(old)}: {old[:65]!r}")
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
            manifest.get("reset_ticket_wake_staged") is not True):
        parser.error("expected nonproduction v18 reset-wakeup candidate")
    records = {r["path"]: r for r in manifest["files"]}
    files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if len(records) != len(manifest["files"]) or files != set(records):
        parser.error("source file set or manifest is ambiguous")
    for name, record in records.items():
        if digest((source / name).read_bytes()) != record["sha256"]:
            parser.error("source hash mismatch: " + name)
    name = "include/wr-iot-mbss-open-admission.inc"
    data = (source / name).read_bytes()
    data = one(data,
        b"VOID wr_iot_mbss_publish_ready(PRTMP_ADAPTER pAd, PNET_DEV pDev, INT BssId);",
        b"VOID wr_iot_mbss_publish_ready(PRTMP_ADAPTER pAd, PNET_DEV pDev, INT BssId);\n"
        b"VOID wr_iot_mbss_publish_down(PRTMP_ADAPTER pAd, PNET_DEV pDev, INT BssId);")
    data = one(data,
        b"    adapter->wr_iot_transition.busy==WR_RADIO_BSS_OPEN&&\n"
        b"    adapter->wr_iot_transition.serial==ticket.serial;",
        b"    adapter->wr_iot_transition.busy==WR_RADIO_BSS_OPEN&&\n"
        b"    adapter->wr_iot_transition.serial==ticket.serial&&\n"
        b"    adapter->wr_iot_transition.epoch==ticket.epoch&&\n"
        b"    adapter->wr_iot_transition.phase==WR_RADIO_READY&&\n"
        b"    adapter->wr_iot_transition.main_ready&&\n"
        b"    !adapter->wr_iot_transition.main_inhibited&&\n"
        b"    !adapter->wr_iot_transition.reset_pending&&\n"
        b"    !adapter->wr_iot_transition.retiring&&\n"
        b"    !adapter->wr_iot_transition.pm_suspending&&\n"
        b"    !adapter->wr_iot_transition.pm_suspended;")
    data = one(data,
        b"    wr_iot_mbss_publish_ready(adapter,pDev,bss_id);\n"
        b"#endif\n"
        b"    RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"   }\n"
        b"   wr_iot_bss_open_finish_observed(",
        b"    wr_iot_mbss_publish_ready(adapter,pDev,bss_id);\n"
        b"#endif\n"
        b"    RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"    /* Pending reset/main-down can latch while the daemon event runs.\n"
        b"     * Compensate before retiring this BSS_OPEN ticket. */\n"
        b"    if(adapter->wr_iot_transition.epoch!=ticket.epoch||\n"
        b"       adapter->wr_iot_transition.phase!=WR_RADIO_READY||\n"
        b"       !adapter->wr_iot_transition.main_ready||\n"
        b"       adapter->wr_iot_transition.main_inhibited||\n"
        b"       adapter->wr_iot_transition.reset_pending||\n"
        b"       adapter->wr_iot_transition.retiring||\n"
        b"       adapter->wr_iot_transition.pm_suspending||\n"
        b"       adapter->wr_iot_transition.pm_suspended){\n"
        b"     RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"#ifdef BAND_STEERING\n"
        b"     wr_iot_mbss_publish_down(adapter,pDev,bss_id);\n"
        b"#endif\n"
        b"     RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"    }\n"
        b"   }\n"
        b"   wr_iot_bss_open_finish_observed(")
    if data.count(b"wr_iot_mbss_publish_down(adapter,pDev,bss_id)") != 1:
        parser.error("steering compensation call is ambiguous")
    shutil.copytree(source, output)
    (output / name).write_bytes(data)
    records[name]["sha256"] = digest(data)
    records[name]["stage"] = records[name].get("stage", "driver") + "+steering-intent-recheck"
    manifest["files"] = list(records.values())
    manifest["mbss_steering_race_staged"] = True
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Staged {len(records)} checked files: {output}")
    print("Pre-event intent check and post-event compensation; no production install")


if __name__ == "__main__":
    main()
