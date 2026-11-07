#!/usr/bin/env python3
"""Compose the conditional reset-ticket wakeup into an isolated IoT tree."""

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
        raise ValueError(f"expected one reviewed reset anchor: {old[:60]!r}")
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
            manifest.get("mbss_open_wake_staged") is not True):
        parser.error("expected nonproduction v17 open-wakeup candidate")
    records = {r["path"]: r for r in manifest["files"]}
    files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if len(records) != len(manifest["files"]) or files != set(records):
        parser.error("source file set or manifest is ambiguous")
    for name, record in records.items():
        if digest((source / name).read_bytes()) != record["sha256"]:
            parser.error("source hash mismatch: " + name)
    name = "include/wr-iot-reset-admission.inc"
    data = (source / name).read_bytes()
    template = Path(__file__).with_name("reset-admission.inc").read_bytes()
    if data.replace(b"\r\n", b"\n") != template.replace(b"\r\n", b"\n"):
        data = one(data, b" int admitted=0;", b" int admitted=0,retired=0;")
        data = one(data,
            b" wr_iot_radio_finish_unverified(&pAd->wr_iot_transition,&ticket);\n"
            b" RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);\n"
            b" rtnl_unlock();",
            b" retired=wr_iot_radio_finish_unverified(&pAd->wr_iot_transition,&ticket);\n"
            b" RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);\n"
            b" rtnl_unlock();\n"
            b" if(retired)wake_up_all(&pAd->wr_iot_ticket_wait);")
    if data.replace(b"\r\n", b"\n") != template.replace(b"\r\n", b"\n"):
        parser.error("staged reset result differs from reviewed shared template")
    shutil.copytree(source, output)
    (output / name).write_bytes(data)
    records[name]["sha256"] = digest(data)
    records[name]["stage"] = records[name].get("stage", "driver") + "+reset-wake"
    manifest["files"] = list(records.values())
    manifest["reset_ticket_wake_staged"] = True
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Staged {len(records)} checked files: {output}")
    print("Conditional reset wake after transition and RTNL unlock; no production install")


if __name__ == "__main__":
    main()
