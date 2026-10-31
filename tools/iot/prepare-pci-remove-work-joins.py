#!/usr/bin/env python3
"""Stage two PCI remove work joins in a separate, nonproduction MT7603 tree."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def once(text: str, old: str, new: str) -> str:
    if text.count(old) != 1:
        raise ValueError("PCI remove insertion anchor changed")
    return text.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        parser.error("output must be new and separate")
    manifest = json.loads((source.parent / (source.name + "-composition.json")).read_text(encoding="utf-8"))
    if manifest.get("production_installed") is not False or \
            manifest.get("pci_root_detach_result_guarded") is not True or \
            manifest.get("main_recovery_work_initialized") is not True:
        parser.error("source is not the reviewed partial PCI candidate")
    for record in manifest["files"]:
        path = source / record["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            parser.error("source changed: " + record["path"])
    name = "os/linux/pci_main_dev.c"
    text = (source / name).read_text(encoding="utf-8")
    old = "\tif (pAd != NULL)\n\t{\n\t\t/* A failed child detach leaves callbacks and references alive."
    first = """\tif (pAd != NULL)
\t{
\t\tPRTMP_ADAPTER adapter = (PRTMP_ADAPTER)pAd;
\t\tULONG flags;
\t\t/* Fence ordinary queue admission before joining a callback. */
\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
\t\twr_iot_radio_retire(&adapter->wr_iot_transition);
\t\twr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery);
\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\tcancel_work_sync(&adapter->wr_iot_main_recovery_work);
\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
\t\tif (adapter->wr_iot_main_recovery.deferred_owners) {
\t\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\treturn; /* Retained owner still fences adapter release. */
\t\t}
\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\t/* A failed child detach leaves callbacks and references alive."""
    text = once(text, old, first)
    old = "\t\tif (!RtmpPhyNetDevExit(pAd, net_dev))\n\t\t\treturn; /* Never free a partially detached adapter. */"
    second = """\t\tif (!RtmpPhyNetDevExit(pAd, net_dev))
\t\t\treturn; /* Never free a partially detached adapter. */
\t\t/* Unregister may have invoked ndo_stop after the first join. */
\t\tcancel_work_sync(&adapter->wr_iot_main_recovery_work);
\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
\t\tif (adapter->wr_iot_main_recovery.deferred_owners) {
\t\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\treturn;
\t\t}
\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);"""
    text = once(text, old, second)
    shutil.copytree(source, output)
    (output / name).write_text(text, encoding="utf-8", newline="\n")
    for record in manifest["files"]:
        if record["path"] == name:
            record["stage"] += "+pci-two-work-joins"
            record["sha256"] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    manifest["pci_remove_two_work_joins_staged"] = True
    manifest["pci_release_gate_bound"] = False
    manifest["complete_driver_tree"] = False
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PASS partial PCI work joins; release observation and owner reap unbound")


if __name__ == "__main__":
    main()
