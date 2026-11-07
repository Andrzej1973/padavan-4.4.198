#!/usr/bin/env python3
"""Check isolated MT7603 remove-result declarations before target compilation."""

import argparse
import re
from pathlib import Path


SIGNATURES = (
    ("MBSS_Remove", "ap/ap_mbss.c", "include/ap_mbss.h"),
    ("WDS_Remove", "ap/ap_wds.c", "include/ap_wds.h"),
    ("ApCli_Remove", "ap/ap_apcli.c", "include/ap_apcli.h"),
    ("Monitor_Remove", "sniffer/sniffer_radiotap.c", "include/rtmp.h"),
    ("RT28xx_MBSS_Remove", "ap/ap_mbss_inf.c", "include/rt_os_net.h"),
    ("RT28xx_WDS_Remove", "ap/ap_wds_inf.c", "include/rt_os_net.h"),
    ("RT28xx_ApCli_Remove", "ap/ap_apcli_inf.c", "include/rt_os_net.h"),
    ("RT28xx_Monitor_Remove", "os/linux/rt_profile.c", "include/rt_os_net.h"),
)


def check(root: Path, name: str, source: str, header: str) -> None:
    declaration = re.compile(r"\b(INT|VOID)\s+" + re.escape(name) + r"\s*\(")
    for relative, terminator in ((source, ")"), (header, ");")):
        path = root / relative
        data = path.read_text(encoding="utf-8", errors="replace")
        matches = list(declaration.finditer(data))
        if len(matches) != 1 or matches[0].group(1) != "INT":
            raise ValueError(f"{relative}: expected one INT {name}, found "
                             f"{[match.group(1) for match in matches]}")
        if terminator == ");" and not re.search(
            r"\bINT\s+" + re.escape(name) + r"\s*\([^;{}]*\)\s*;",
            data[matches[0].start():], re.S,
        ):
            raise ValueError(f"{relative}: {name} declaration is incomplete")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("driver", type=Path)
    args = parser.parse_args()
    try:
        for signature in SIGNATURES:
            check(args.driver, *signature)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(f"Checked {len(SIGNATURES)} remove-result source/header pairs")


if __name__ == "__main__":
    main()
