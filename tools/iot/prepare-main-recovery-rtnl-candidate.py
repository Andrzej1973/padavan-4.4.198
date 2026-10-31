#!/usr/bin/env python3
"""Stage the nonblocking RTNL recovery callback in an isolated IoT tree."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if output.exists() or source in output.parents or output in source.parents:
        parser.error("output must be new and separate")
    manifest = source.parent / (source.name + "-composition.json")
    base = json.loads(manifest.read_text(encoding="utf-8"))
    records = {row["path"]: row for row in base["files"]}
    files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if (base.get("production_installed") is not False or
            base.get("main_verify_checked_rollback_staged") is not True or
            len(records) != len(base["files"]) or files != set(records)):
        parser.error("expected intact isolated v21 composition")
    for name, row in records.items():
        if digest(source / name) != row["sha256"]:
            parser.error("source hash mismatch: " + name)

    main_name = "os/linux/rt_main_dev.c"
    owner_name = "include/main-open-recovery-owner.h"
    old = """ adapter = container_of(work, RTMP_ADAPTER, wr_iot_main_recovery_work);
 (void)wr_iot_main_recovery_execute(adapter);
}"""
    new = """ adapter = container_of(work, RTMP_ADAPTER, wr_iot_main_recovery_work);
 /* PCI removal may join this callback while another owner holds RTNL.
  * Never block a cancel_work_sync waiter on rtnl_lock. */
 if (!rtnl_trylock()) {
  ULONG flags;
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
  wr_iot_main_recovery_rtnl_unavailable(&adapter->wr_iot_main_recovery);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  return;
 }
 (void)wr_iot_main_recovery_execute(adapter);
 rtnl_unlock();
}"""
    data = (source / main_name).read_text(encoding="utf-8")
    anchor = '#include "mt7603-main-observe.h"'
    if data.count(old) != 1 or data.count(anchor) != 1:
        parser.error("reviewed worker or include anchor changed")
    data = data.replace(anchor, anchor + "\n#include <linux/rtnetlink.h>", 1)
    data = data.replace(old, new, 1)
    owner = Path(__file__).with_name("main-open-recovery-owner.h")
    owner_data = owner.read_text(encoding="utf-8")
    if owner_data.count("wr_iot_main_recovery_rtnl_unavailable(") != 1:
        parser.error("RTNL-unavailable owner transition missing")
    shutil.copytree(source, output)
    (output / main_name).write_text(data, encoding="utf-8", newline="\n")
    (output / owner_name).write_text(owner_data, encoding="utf-8", newline="\n")
    for name in (main_name, owner_name):
        records[name]["sha256"] = digest(output / name)
        records[name]["stage"] += "+nonblocking-recovery-rtnl"
    base["main_recovery_rtnl_trylock_staged"] = True
    base["main_recovery_queue_bound"] = False
    base["pci_release_gate_bound"] = False
    base["production_installed"] = False
    target = output.parent / (output.name + "-composition.json")
    target.write_text(json.dumps(base, indent=2) + "\n", encoding="utf-8")
    print("PASS staged nonblocking RTNL callback; queue/removal remain unbound")


if __name__ == "__main__":
    main()
