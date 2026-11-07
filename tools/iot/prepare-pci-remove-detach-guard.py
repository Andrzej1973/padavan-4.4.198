#!/usr/bin/env python3
"""Stage a fail-closed root-detach guard in a separate partial MT7603 tree."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


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
            manifest.get("main_recovery_work_initialized") is not True or \
            manifest.get("pci_release_gate_bound") is not False:
        parser.error("source is not the reviewed partial work candidate")
    for record in manifest["files"]:
        path = source / record["path"]
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != record["sha256"]:
            parser.error("source changed: " + record["path"])
    name = "os/linux/pci_main_dev.c"
    before = (source / name).read_text(encoding="utf-8")
    old = "\t\t/* Unregister/Free all allocated net_device. */\n\t\tRtmpPhyNetDevExit(pAd, net_dev);"
    new = ("\t\t/* A failed child detach leaves callbacks and references alive.\n"
           "\t\t * Keep adapter/CSR ownership rather than free live memory. */\n"
           "\t\tif (!RtmpPhyNetDevExit(pAd, net_dev))\n"
           "\t\t\treturn; /* Never free a partially detached adapter. */")
    if before.count(old) != 1:
        parser.error("root detach baseline changed")
    shutil.copytree(source, output)
    (output / name).write_text(before.replace(old, new, 1), encoding="utf-8", newline="\n")
    for record in manifest["files"]:
        if record["path"] == name:
            record["stage"] += "+pci-root-detach-guard"
            record["sha256"] = hashlib.sha256((output / name).read_bytes()).hexdigest()
    manifest["pci_root_detach_result_guarded"] = True
    manifest["pci_release_gate_bound"] = False
    manifest["complete_driver_tree"] = False
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("PASS partial PCI root-detach guard; work joins/release still unbound")


if __name__ == "__main__":
    main()
