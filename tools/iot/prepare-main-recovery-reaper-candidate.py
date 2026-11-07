#!/usr/bin/env python3
"""Stage an isolated main recovery queue and joined reaper for source review."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_one(data: str, old: str, new: str, name: str) -> str:
    if data.count(old) != 1:
        raise ValueError(f"{name}: expected one reviewed anchor, found {data.count(old)}")
    return data.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source in output.parents or output in source.parents:
        parser.error("output must be new and separate")
    base = json.loads((source.parent / (source.name + "-composition.json")).read_text(encoding="utf-8"))
    records = {row["path"]: row for row in base["files"]}
    files = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if (base.get("production_installed") is not False or
            base.get("main_recovery_rtnl_trylock_staged") is not True or
            files != set(records) or len(records) != len(base["files"])):
        parser.error("expected intact isolated v22 candidate")
    for name, row in records.items():
        if digest(source / name) != row["sha256"]:
            parser.error("source hash mismatch: " + name)

    main_name = "os/linux/rt_main_dev.c"
    owner_name = "include/main-open-recovery-owner.h"
    main_source = (source / main_name).read_text(encoding="utf-8")
    new_helpers = Path(__file__).with_name("main-recovery-reaper.inc").read_text(encoding="utf-8")
    marker = "int MainVirtualIF_open(struct net_device *net_dev)"
    main_source = replace_one(main_source, marker, new_helpers + "\n" + marker, main_name)
    old = """  if (wr_iot_main_close_begin_checked(adapter,net_dev,&close_ticket,
        &close_generation,&close_token,&wait_serial)==0 &&
      close_generation==generation &&
      wr_iot_main_close_preclose_once(adapter,net_dev,close_generation,
                                     &close_ticket)==0 &&
      wr_iot_main_close_continue_checked(adapter,net_dev,close_generation,
                                         close_token,&close_ticket)==0)
   closed=1;
  if (closed)
   RT_MOD_DEC_USE_COUNT();
  else
   DBGPRINT(RT_DEBUG_ERROR,
    ("MT7603 main VERIFY failed; checked close incomplete, retaining owner\\n"));"""
    new = """  int began=wr_iot_main_close_begin_checked(adapter,net_dev,&close_ticket,
        &close_generation,&close_token,&wait_serial)==0;
  if (began && close_generation==generation &&
      wr_iot_main_close_preclose_once(adapter,net_dev,close_generation,
                                     &close_ticket)==0 &&
      wr_iot_main_close_continue_checked(adapter,net_dev,close_generation,
                                         close_token,&close_ticket)==0)
   closed=1;
  if (closed)
   RT_MOD_DEC_USE_COUNT();
  else if (!wr_iot_main_verify_recovery_submit(adapter,net_dev,generation,
             began && close_generation==generation ? &close_ticket : NULL))
   DBGPRINT(RT_DEBUG_ERROR,
    ("MT7603 main VERIFY failed; recovery admission rejected, retaining pin\\n"));"""
    main_source = replace_one(main_source, old, new, main_name)

    rtmp_name = "include/rtmp.h"
    rtmp_source = (source / rtmp_name).read_text(encoding="utf-8")
    rtmp_source = replace_one(rtmp_source,
        "\tstruct work_struct wr_iot_main_recovery_work;",
        "\tstruct work_struct wr_iot_main_recovery_work;\n\tstruct delayed_work wr_iot_main_recovery_reap_work;", rtmp_name)
    rtmp_source = replace_one(rtmp_source,
        "VOID wr_iot_main_recovery_work_fn(struct work_struct *work);",
        "VOID wr_iot_main_recovery_work_fn(struct work_struct *work);\n"
        "VOID wr_iot_main_recovery_reap_work_fn(struct work_struct *work);\n"
        "INT wr_iot_main_recovery_join_complete(RTMP_ADAPTER *adapter);", rtmp_name)

    init_name = "common/rtmp_init.c"
    init_source = (source / init_name).read_text(encoding="utf-8")
    init_source = replace_one(init_source,
        "\t\tINIT_WORK(&pAd->wr_iot_main_recovery_work, wr_iot_main_recovery_work_fn);",
        "\t\tINIT_WORK(&pAd->wr_iot_main_recovery_work, wr_iot_main_recovery_work_fn);\n"
        "\t\tINIT_DELAYED_WORK(&pAd->wr_iot_main_recovery_reap_work, wr_iot_main_recovery_reap_work_fn);", init_name)

    pci_name = "os/linux/pci_main_dev.c"
    pci_source = (source / pci_name).read_text(encoding="utf-8")
    old_join = "\t\tcancel_work_sync(&adapter->wr_iot_main_recovery_work);"
    new_join = "\t\tcancel_delayed_work_sync(&adapter->wr_iot_main_recovery_reap_work);\n" + old_join + "\n\t\twr_iot_main_recovery_join_complete(adapter);"
    if pci_source.count(old_join) != 2:
        parser.error("PCI remove join count changed")
    pci_source = pci_source.replace(old_join, new_join)
    # Probe unwind has no recovery owner but still joins the new delayed work.
    pci_source = replace_one(pci_source,
        "\tcancel_work_sync(&pAd->wr_iot_main_recovery_work);",
        "\tcancel_delayed_work_sync(&pAd->wr_iot_main_recovery_reap_work);\n"
        "\tcancel_work_sync(&pAd->wr_iot_main_recovery_work);", pci_name)

    shutil.copytree(source, output)
    owner_source = Path(__file__).with_name("main-open-recovery-owner.h").read_text(encoding="utf-8")
    if owner_source.count("wr_iot_main_recovery_canceled_before_run(") != 1:
        parser.error("canceled pending-work transition missing")
    for name, data in ((main_name, main_source), (rtmp_name, rtmp_source),
                       (init_name, init_source), (pci_name, pci_source),
                       (owner_name, owner_source)):
        (output / name).write_text(data, encoding="utf-8", newline="\n")
        records[name]["sha256"] = digest(output / name)
        records[name]["stage"] += "+main-recovery-queue-reaper"
    base["main_recovery_queue_bound"] = True
    base["main_recovery_reaper_staged"] = True
    base["pci_release_gate_bound"] = False
    base["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(base, indent=2) + "\n", encoding="utf-8")
    print("PASS staged main recovery queue/reaper; PCI incomplete-owner path remains open")


if __name__ == "__main__":
    main()
