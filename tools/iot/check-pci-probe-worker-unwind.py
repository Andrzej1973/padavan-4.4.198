#!/usr/bin/env python3
"""Fail closed until a candidate joins main recovery work on probe failure.

This is a source-order preflight, not a proof of work ownership or runtime
quiescence. A passing source still needs target compilation and fault tests.
"""

import argparse
from pathlib import Path


def issues(root: Path) -> list[str]:
    source = (root / "os/linux/pci_main_dev.c").read_text(encoding="utf-8")
    adapter = (root / "include/rtmp.h").read_text(encoding="utf-8")
    result = []
    if "wr_iot_main_recovery_work" not in adapter:
        result.append("adapter-owned main recovery work item is absent")
    try:
        start = source.index("err_out_free_netdev:")
        next_label = source.index("err_out_iounmap:", start)
        unwind = source[start:next_label]
        free = unwind.index("RTMPFreeAdapter(pAd)")
    except ValueError:
        result.append("probe failure labels or adapter free changed")
        return result
    if "cancel_work_sync(&pAd->wr_iot_main_recovery_work)" not in unwind[:free]:
        result.append("probe failure frees adapter without joining main recovery work")
    if "pci_set_drvdata(pdev, NULL)" not in unwind[:free]:
        result.append("probe failure does not clear PCI driver data before free")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    found = issues(args.candidate.resolve(strict=True))
    for item in found:
        print("OPEN GATE: " + item)
    if found:
        return 1
    print("SOURCE PREFLIGHT PASS; verify worker state and target fault paths")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
