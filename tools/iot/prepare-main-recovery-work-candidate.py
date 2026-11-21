#!/usr/bin/env python3
"""Stage adapter-owned main recovery work and probe-unwind join in a new tree.

This is deliberately partial: no queue admission or PCI remove release is bound.
"""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def replace_once(value: str, old: str, new: str) -> str:
    if value.count(old) != 1:
        raise ValueError("changed insertion anchor: " + old[:80])
    return value.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source, output = args.source.resolve(strict=True), args.output.resolve()
    if output.exists() or source == output or source in output.parents or output in source.parents:
        parser.error("output must be new and separate")
    manifest_path = source.parent / (source.name + "-composition.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("production_installed") is not False or \
            manifest.get("main_close_deferred_executor_staged") is not True or \
            manifest.get("main_close_recovery_bound") is not False:
        parser.error("input is not the reviewed partial main recovery bundle")
    for record in manifest["files"]:
        path = source / record["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            parser.error("input changed: " + record["path"])
    files = {}
    for name in ("include/rtmp.h", "common/rtmp_init.c",
                 "os/linux/rt_main_dev.c", "os/linux/pci_main_dev.c"):
        files[name] = (source / name).read_text(encoding="utf-8")
    files["include/rtmp.h"] = replace_once(
        files["include/rtmp.h"], "#include <linux/wait.h>",
        "#include <linux/wait.h>\n#include <linux/workqueue.h>")
    files["include/rtmp.h"] = replace_once(
        files["include/rtmp.h"],
        "/* Deferred main-open recovery state; workqueue binding pending. */\n"
        "\tstruct wr_iot_main_recovery_owner wr_iot_main_recovery;",
        "/* Deferred main recovery; queue and PCI remove binding pending. */\n"
        "\tstruct wr_iot_main_recovery_owner wr_iot_main_recovery;\n"
        "\tstruct work_struct wr_iot_main_recovery_work;")
    files["include/rtmp.h"] = replace_once(
        files["include/rtmp.h"],
        "VOID wr_iot_radio_reset_drain(RTMP_ADAPTER *pAd);",
        "VOID wr_iot_radio_reset_drain(RTMP_ADAPTER *pAd);\n"
        "VOID wr_iot_main_recovery_work_fn(struct work_struct *work);")
    files["common/rtmp_init.c"] = replace_once(
        files["common/rtmp_init.c"],
        "\t\twr_iot_main_recovery_init(&pAd->wr_iot_main_recovery);",
        "\t\twr_iot_main_recovery_init(&pAd->wr_iot_main_recovery);\n"
        "\t\tINIT_WORK(&pAd->wr_iot_main_recovery_work, wr_iot_main_recovery_work_fn);")
    if files["os/linux/rt_main_dev.c"].count(
            "static int wr_iot_main_recovery_execute(PRTMP_ADAPTER adapter)") != 1:
        parser.error("reviewed deferred executor changed")
    callback = """\n/* Only the external reaper may join this work and reset the owner. Queue
 * admission must hold a netdev reference and fence adapter release first. */
VOID wr_iot_main_recovery_work_fn(struct work_struct *work)
{
 PRTMP_ADAPTER adapter;
 if (!work) return;
 adapter = container_of(work, RTMP_ADAPTER, wr_iot_main_recovery_work);
 (void)wr_iot_main_recovery_execute(adapter);
}
"""
    if "wr_iot_main_recovery_work_fn(struct work_struct *work)" in files["os/linux/rt_main_dev.c"]:
        parser.error("worker callback already present")
    files["os/linux/rt_main_dev.c"] += callback
    files["os/linux/pci_main_dev.c"] = replace_once(
        files["os/linux/pci_main_dev.c"],
        "err_out_free_netdev:\n\t/* Attach failed after pci_set_drvdata and netdev_ops allocation. */",
        "err_out_free_netdev:\n"
        "\t/* Join outside the adapter lock before dropping netdev or adapter. */\n"
        "\tcancel_work_sync(&pAd->wr_iot_main_recovery_work);\n"
        "\t/* Attach failed after pci_set_drvdata and netdev_ops allocation. */")
    shutil.copytree(source, output)
    for name, value in files.items():
        (output / name).write_text(value, encoding="utf-8", newline="\n")
    for record in manifest["files"]:
        if record["path"] in files:
            record["stage"] += "+main-work-probe-partial"
            record["sha256"] = hashlib.sha256((output / record["path"]).read_bytes()).hexdigest()
    manifest["main_recovery_work_initialized"] = True
    manifest["main_recovery_probe_unwind_join_staged"] = True
    manifest["main_close_recovery_bound"] = False
    manifest["pci_release_gate_bound"] = False
    manifest["complete_driver_tree"] = False
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PASS partial work callback/init/probe join; queue/remove still unbound")


if __name__ == "__main__":
    main()
