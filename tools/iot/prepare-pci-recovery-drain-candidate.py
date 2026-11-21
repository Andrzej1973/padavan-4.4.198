#!/usr/bin/env python3
"""Stage an isolated PCI recovery drain before stopping main recovery work."""

import argparse
import hashlib
import json
import shutil
from pathlib import Path


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replace_once(source: str, old: str, new: str, name: str) -> str:
    if source.count(old) != 1:
        raise ValueError(f"{name}: reviewed anchor count is {source.count(old)}")
    return source.replace(old, new, 1)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    output = args.output.resolve()
    if output.exists() or source in output.parents or output in source.parents:
        parser.error("output must be a new separate directory")
    manifest_path = source.parent / (source.name + "-composition.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    records = {row["path"]: row for row in manifest["files"]}
    if (manifest.get("production_installed") is not False or
            manifest.get("main_recovery_reaper_staged") is not True or
            manifest.get("pci_release_gate_bound") is not False):
        parser.error("expected nonproduction v23b reaper candidate")
    actual = {p.relative_to(source).as_posix() for p in source.rglob("*") if p.is_file()}
    if actual != set(records):
        parser.error("source file inventory differs from manifest")
    for name, record in records.items():
        if sha(source / name) != record["sha256"]:
            parser.error("source hash mismatch: " + name)

    rtmp_name = "include/rtmp.h"
    rtmp = (source / rtmp_name).read_text(encoding="utf-8")
    rtmp = replace_once(rtmp, '#include "main-open-recovery-owner.h"',
                        '#include "main-open-recovery-owner.h"\n#include "pci-retirement-owner.h"', rtmp_name)
    rtmp = replace_once(rtmp,
                        "\tstruct wr_iot_main_recovery_owner wr_iot_main_recovery;",
                        "\tstruct wr_iot_main_recovery_owner wr_iot_main_recovery;\n"
                        "\tstruct wr_iot_pci_retirement wr_iot_pci_retirement;", rtmp_name)

    init_name = "common/rtmp_init.c"
    init = (source / init_name).read_text(encoding="utf-8")
    init = replace_once(init, "\t\twr_iot_main_recovery_init(&pAd->wr_iot_main_recovery);",
                        "\t\twr_iot_main_recovery_init(&pAd->wr_iot_main_recovery);\n"
                        "\t\twr_iot_pci_retirement_init(&pAd->wr_iot_pci_retirement);", init_name)

    pci_name = "os/linux/pci_main_dev.c"
    pci = (source / pci_name).read_text(encoding="utf-8")
    marker = "static VOID DEVEXIT rt_pci_remove(struct pci_dev *pci_dev)"
    helper = Path(__file__).with_name("pci-recovery-drain.inc").read_text(encoding="utf-8")
    pci = replace_once(pci, marker, helper + "\n" + marker, pci_name)
    old = """\t\twr_iot_radio_retire(&adapter->wr_iot_transition);
\t\twr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery);
\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\tcancel_delayed_work_sync(&adapter->wr_iot_main_recovery_reap_work);"""
    new = """\t\twr_iot_radio_retire(&adapter->wr_iot_transition);
\t\tif (!wr_iot_pci_retirement_begin(&adapter->wr_iot_pci_retirement,
\t\t    &adapter->wr_iot_transition, 1) ||
\t\t    !wr_iot_pci_retirement_drain_begin(&adapter->wr_iot_pci_retirement)) {
\t\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\treturn;
\t\t}
\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\tif (!wr_iot_pci_recovery_drain(adapter))
\t\t\treturn; /* Still-owned recovery blocks this isolated candidate. */
\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
\t\twr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery);
\t\twr_iot_pci_retirement_stop_requested(&adapter->wr_iot_pci_retirement, 1);
\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\tcancel_delayed_work_sync(&adapter->wr_iot_main_recovery_reap_work);"""
    pci = replace_once(pci, old, new, pci_name)

    shutil.copytree(source, output)
    replacements = {rtmp_name: rtmp, init_name: init, pci_name: pci}
    for name, text in replacements.items():
        (output / name).write_text(text, encoding="utf-8", newline="\n")
        records[name]["sha256"] = sha(output / name)
        records[name]["stage"] += "+pci-recovery-drain"
    for name in ("pci-retirement-owner.h", "adapter-release-gate.h"):
        relative = "include/" + name
        destination = output / relative
        shutil.copyfile(Path(__file__).with_name(name), destination)
        records[relative] = {"path": relative, "stage": "pci-recovery-drain",
                             "purpose": "driver", "sha256": sha(destination)}
    manifest["files"] = list(records.values())
    manifest["pci_recovery_drain_staged"] = True
    manifest["pci_release_gate_bound"] = False
    manifest["production_installed"] = False
    (output.parent / (output.name + "-composition.json")).write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"PASS isolated PCI recovery drain staged; {len(records)} hashes recorded")


if __name__ == "__main__":
    main()
