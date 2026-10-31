#!/usr/bin/env python3
"""Stage post-unlock MBSS-open ticket wakeups in a verified isolated tree."""

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
        raise ValueError(f"expected one reviewed anchor, found {data.count(old)}: {old[:60]!r}")
    return data.replace(old, new, 1)


def two(data: bytes, old: bytes, new: bytes) -> bytes:
    nl = b"\r\n" if b"\r\n" in data else b"\n"
    old, new = old.replace(b"\n", nl), new.replace(b"\n", nl)
    if data.count(old) != 2:
        raise ValueError(f"expected two reviewed failure branches, found {data.count(old)}")
    return data.replace(old, new)


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
            manifest.get("mbss_steering_down_staged") is not True):
        parser.error("expected nonproduction v16b steering candidate")
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
        b"int admitted,ret,observe_iot,bss_id=0,observed_bss=0,publish_ready=0;",
        b"int admitted,ret,observe_iot,bss_id=0,observed_bss=0,publish_ready=0,retired=0;")
    data = one(data,
        b"  wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);\n  admitted=0;",
        b"  retired=wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);\n  admitted=0;")
    data = one(data,
        b" RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n if(!admitted)return -1;",
        b" RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b" if(!admitted){\n"
        b"  if(retired)wake_up_all(&adapter->wr_iot_ticket_wait);\n"
        b"  return -1;\n"
        b" }")
    data = one(data,
        b"  wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,0);\n"
        b"  wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);\n"
        b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"  return -1;",
        b"  wr_iot_ref_open_finish(record,pDev,record->generation,ticket.serial,0);\n"
        b"  retired=wr_iot_radio_abort_bss_open_unmutated(&adapter->wr_iot_transition,&ticket);\n"
        b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"  if(retired)wake_up_all(&adapter->wr_iot_ticket_wait);\n"
        b"  return -1;")
    data = two(data,
        b"  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);\n"
        b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"  return -1;",
        b"  retired=wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);\n"
        b"  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b"  if(retired)wake_up_all(&adapter->wr_iot_ticket_wait);\n"
        b"  return -1;")
    data = one(data,
        b"  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);\n"
        b" }\n RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n return ret;",
        b"  wr_iot_radio_finish(&adapter->wr_iot_transition,&ticket,0);\n"
        b" }\n"
        b" /* Wake after either verified or unverified retirement, never while the\n"
        b"  * transition IRQ lock is held. A failed finish retains the ticket. */\n"
        b" retired=adapter->wr_iot_transition.busy==0&&\n"
        b"  adapter->wr_iot_transition.retired_serial==ticket.serial;\n"
        b" RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);\n"
        b" if(retired)wake_up_all(&adapter->wr_iot_ticket_wait);\n"
        b" return ret;")
    if data.count(b"wake_up_all(&adapter->wr_iot_ticket_wait);") != 5:
        parser.error("expected five post-unlock retirement wake sites")
    shutil.copytree(source, output)
    (output / name).write_bytes(data)
    records[name]["sha256"] = digest(data)
    records[name]["stage"] = records[name].get("stage", "driver") + "+mbss-open-wake"
    manifest["files"] = list(records.values())
    manifest["mbss_open_wake_staged"] = True
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Staged {len(records)} checked files: {output}")
    print("Five post-unlock wake sites; no production install")


if __name__ == "__main__":
    main()
