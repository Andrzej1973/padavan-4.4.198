#!/usr/bin/env python3
"""Reject an isolated MT76x3 candidate with an unbound PCI release sequence.

This is a source-order preflight only. A pass is not target or runtime proof.
"""

import argparse
import re
from pathlib import Path


def function(source: str, signature: str) -> str:
    if source.count(signature) != 1:
        raise ValueError(f"expected one {signature!r} definition")
    start = source.index(signature)
    opening = source.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        if end >= len(source):
            raise ValueError(f"unterminated {signature!r}")
        depth += (source[end] == "{") - (source[end] == "}")
        end += 1
    return source[start:end]


def detach_result_checked(remove: str) -> bool:
    """Require the fallible detach call itself to guard the release path.

    A nearby unrelated `if` is not evidence that FALSE prevents adapter free.
    Keep this preflight conservative; review other control-flow forms manually.
    """
    call = r"RtmpPhyNetDevExit\s*\(\s*pAd\s*,\s*net_dev\s*\)"
    return bool(re.search(r"if\s*\(\s*!\s*" + call + r"\s*\)\s*\{?\s*return\s*;", remove))


def child_result_issues(detach: str) -> list[str]:
    """All child families must stop root detach on a rejected removal.

    The C source includes optional families behind preprocessor guards. Check
    their source paths here; build-specific presence is a separate target gate.
    """
    issues = []
    for name in ("ApCli", "WDS", "MBSS", "Monitor"):
        call = r"RT28xx_" + name + r"_Remove\s*\(\s*pAd\s*\)"
        guard = (r"if\s*\(\s*" + call +
                 r"\s*!=\s*NDIS_STATUS_SUCCESS\s*\)\s*\{?\s*return\s+FALSE\s*;")
        if len(re.findall(guard, detach)) != 1:
            issues.append(f"{name} removal does not guard root detach")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path)
    args = parser.parse_args()
    root = args.candidate.resolve(strict=True)
    remove = function((root / "os/linux/pci_main_dev.c").read_text(encoding="utf-8"),
                      "static VOID DEVEXIT rt_pci_remove(")
    detach = function((root / "os/linux/rt_main_dev.c").read_text(encoding="utf-8"),
                      "BOOLEAN RtmpPhyNetDevExit(")
    issues = []
    issues.extend(child_result_issues(detach))
    if not issues:
        call = re.search(r"RtmpPhyNetDevExit\s*\(\s*pAd\s*,\s*net_dev\s*\)", remove)
        if call is None:
            issues.append("root detach result is not observed")
        elif not detach_result_checked(remove):
            issues.append("fallible root detach result does not guard adapter release")
    first_join = remove.find("wr_iot_pci_retirement_work_joined(")
    detach_pos = remove.find("RtmpPhyNetDevExit(pAd, net_dev)")
    second_join = remove.find("wr_iot_pci_retirement_final_work_joined(")
    release = remove.find("wr_iot_pci_retirement_claim_release(")
    free = remove.find("RtmpRaDevCtrlExit(pAd)")
    if min(first_join, detach_pos, second_join, release, free) < 0 or not \
            first_join < detach_pos < second_join < release < free:
        issues.append("first join, root detach, final join and release claim are not ordered before adapter free")
    joins = [match.start() for match in re.finditer(
        r"(?:cancel_work_sync|flush_work)\s*\(\s*&adapter->wr_iot_main_recovery_work\s*\)",
        remove)]
    if len(joins) != 2 or not joins[0] < detach_pos < joins[1] < free:
        issues.append("main recovery work must be joined before and after root detach")
    if issues:
        for issue in issues:
            print("OPEN GATE: " + issue)
        return 1
    print("SOURCE PREFLIGHT PASS; inspect control flow and verify target/runtime separately")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
