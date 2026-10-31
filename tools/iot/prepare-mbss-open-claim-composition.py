#!/usr/bin/env python3
"""Bind MBSS raw open to the existing claimed virtual-UP in an isolated tree.

The source is the v12 checked-stop successor of a hash-verified v11 overlay.
No production driver or release claim is installed by this preparer.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def replace_one(data: bytes, old: bytes, new: bytes, name: str) -> bytes:
    newline = b"\r\n" if b"\r\n" in data else b"\n"
    old, new = old.replace(b"\n", newline), new.replace(b"\n", newline)
    if data.count(old) != 1:
        raise ValueError(f"{name}: expected one reviewed anchor, found {data.count(old)}")
    return data.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("base", type=Path, help="v11 candidate with composition manifest")
    parser.add_argument("source", type=Path, help="v12 checked-stop successor")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    base, source, output = (path.resolve() for path in (args.base, args.source, args.output))
    if not base.is_dir() or not source.is_dir() or output.exists() or \
            base == source or source in output.parents or output in source.parents:
        parser.error("base/source must exist; output must be new and separate")
    composition = json.loads((base.parent / (base.name + "-composition.json")).read_text(encoding="utf-8"))
    stop_report = json.loads((source.parent / (source.name + ".manifest.json")).read_text(encoding="utf-8"))
    if composition.get("production_installed") is not False or \
            stop_report.get("checked_stop_bound") is not True or \
            stop_report.get("recovery_owner_bound") is not False:
        parser.error("expected reviewed nonproduction v11/v12 chain")
    changed_stop = "ap/ap_mbss_inf.c"
    records = {record["path"]: record for record in composition["files"]}
    if len(records) != len(composition["files"]) or changed_stop not in records:
        parser.error("base manifest is incomplete or contains duplicate paths")
    for name, record in records.items():
        base_bytes = (base / name).read_bytes()
        source_bytes = (source / name).read_bytes()
        if sha(base_bytes) != record["sha256"] or \
                (name != changed_stop and source_bytes != base_bytes):
            parser.error("v11/v12 source differs outside reviewed stop change: " + name)
    if sha((base / changed_stop).read_bytes()) != stop_report["source_sha256"] or \
            sha((source / changed_stop).read_bytes()) != stop_report["output_sha256"]:
        parser.error("checked-stop source or output hash changed")
    source_files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if source_files != set(records):
        parser.error("v12 file set differs from the v11 composition manifest")
    dispatcher = (source / "common/cmm_cfg.c").read_bytes()
    header = (source / "include/rt_os_net.h").read_bytes()
    if dispatcher.count(b"wr_iot_virtual_open_claim_matches(&claim,") != 1 or \
            header.count(b"__inline INT VIRTUAL_IF_UP_CLAIM(") != 1:
        parser.error("shared claimed-UP dispatcher is missing or ambiguous")

    raw_name = "ap/ap_mbss_inf.c"
    admission_name = "include/wr-iot-mbss-open-admission.inc"
    raw = (source / raw_name).read_bytes()
    raw = replace_one(raw, b"static INT wr_iot_mbss_open_raw(PNET_DEV pDev)",
                      b"static INT wr_iot_mbss_open_raw(PNET_DEV pDev,\n"
                      b" const struct wr_iot_radio_ticket *ticket, unsigned long generation)", raw_name)
    raw = replace_one(raw, b"VIRTUAL_IF_UP(pAd) != 0",
                      b"VIRTUAL_IF_UP_CLAIM(pAd, pDev, ticket, generation) != 0", raw_name)
    raw = replace_one(
        raw,
        b'\t\t\tDBGPRINT(RT_DEBUG_ERROR, ("MBSS open abort failed\\n"));',
        b'\t\t{ DBGPRINT(RT_DEBUG_ERROR, ("MBSS open abort failed\\n"));\n'
        b'\t\t  return -2; /* retain module pin: vendor state is uncertain */ }',
        raw_name,
    )
    admission = replace_one((source / admission_name).read_bytes(),
                            b"ret=wr_iot_mbss_open_raw(pDev);",
                            b"ret=wr_iot_mbss_open_raw(pDev,&ticket,record->generation);", admission_name)
    if raw.count(b"VIRTUAL_IF_UP_CLAIM(pAd, pDev, ticket, generation)") != 1 or \
            admission.count(b"wr_iot_mbss_open_raw(pDev,&ticket,record->generation)") != 1:
        parser.error("composed MBSS ticket flow is ambiguous")
    shutil.copytree(source, output)
    (output / raw_name).write_bytes(raw)
    (output / admission_name).write_bytes(admission)
    for name, record in records.items():
        record["sha256"] = sha((output / name).read_bytes())
        if name in (raw_name, admission_name):
            record["stage"] = record.get("stage", "driver") + "+mbss-open-claim"
    composition["files"] = list(records.values())
    composition["mbss_checked_stop_bound"] = True
    composition["mbss_open_claim_composed"] = True
    composition["mbss_failed_open_recovery_bound"] = False
    composition["pci_release_gate_bound"] = False
    composition["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(composition, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Composed {len(records)} checked files: {output}")
    print("Open recovery and PCI release remain unbound; no production install")


if __name__ == "__main__":
    main()
