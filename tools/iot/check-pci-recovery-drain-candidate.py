#!/usr/bin/env python3
"""Check isolated PCI drain composition and reviewed remove ordering."""

import argparse
import hashlib
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    candidate = args.candidate.resolve(strict=True)
    manifest = json.loads(
        (candidate.parent / (candidate.name + "-composition.json")).read_text()
    )
    rows = manifest["files"]
    expected = {row["path"] for row in rows}
    actual = {p.relative_to(candidate).as_posix() for p in candidate.rglob("*") if p.is_file()}
    assert len(rows) == len(expected) == 69 and actual == expected
    for row in rows:
        assert hashlib.sha256((candidate / row["path"]).read_bytes()).hexdigest() == row["sha256"]
    assert manifest["pci_recovery_drain_staged"] is True
    assert manifest["pci_release_gate_bound"] is False
    assert manifest["production_installed"] is False
    pci = (candidate / "os/linux/pci_main_dev.c").read_text()
    remove = pci[pci.index("static VOID DEVEXIT rt_pci_remove("):]
    sequence = (
        "wr_iot_radio_retire(&adapter->wr_iot_transition)",
        "wr_iot_pci_retirement_drain_begin(&adapter->wr_iot_pci_retirement)",
        "wr_iot_pci_recovery_drain(adapter)",
        "wr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery)",
        "cancel_delayed_work_sync(&adapter->wr_iot_main_recovery_reap_work)",
    )
    positions = [remove.index(token) for token in sequence]
    assert positions == sorted(positions)
    helper = pci[pci.index("static int wr_iot_pci_recovery_drain("):
                 pci.index("static VOID DEVEXIT rt_pci_remove(")]
    for token in ("flush_delayed_work(", "flush_work(",
                  "wr_iot_main_recovery_join_complete(",
                  "wr_iot_pci_retirement_drain_next(",
                  "wr_iot_pci_retirement_drain_complete("):
        assert helper.count(token) == 1
    assert "if (!wr_iot_pci_recovery_drain(adapter))" in remove
    print("PASS isolated PCI drain: 69 hashes and retire/drain/stop/join ordering")


if __name__ == "__main__":
    main()
