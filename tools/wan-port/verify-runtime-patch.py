#!/usr/bin/env python3
"""Structural checks for the applied runtime WAN-port override patch.

This is not a compiler and does not prove the driver builds: the full MIPS
cross-compile is the build evidence. These cheap invariants catch an
unapplied or partially applied patch, a runtime identifier that leaked into a
preprocessor condition, and a runtime value used where C needs a constant.
"""
import argparse
import re
from pathlib import Path

DRIVER = "trunk/linux-4.4.x/drivers/net/ethernet/raeth/mtk_esw/ioctl_mt762x.c"
DISPATCHER = "trunk/linux-4.4.x/drivers/net/ethernet/raeth/mtk_esw/ioctl.c"
UAPI = "trunk/linux-4.4.x/drivers/net/ethernet/raeth/mtk_esw/ioctl.h"


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="applied Padavan tree root")
    args = parser.parse_args()

    esw = args.tree / "trunk/linux-4.4.x/drivers/net/ethernet/raeth/mtk_esw"
    driver = (esw / Path(DRIVER).name).read_text(encoding="utf-8")
    dispatcher = (esw / Path(DISPATCHER).name).read_text(encoding="utf-8")
    uapi = (esw / Path(UAPI).name).read_text(encoding="utf-8")

    failures = []

    def require(condition, message):
        if not condition:
            failures.append(message)

    # Preprocessor conditions keep the compile-time board macros.
    require("#if (MASK_WAN_PORT_X == 0 && WAN_PORT_X < 5)" in driver,
            "preprocessor guard no longer uses the compile-time WAN macros")
    for line in driver.splitlines():
        if line.lstrip().startswith("#"):
            require("g_wan_port_x" not in line and "g_mask_wan_port_x" not in line,
                    "runtime override leaked into a preprocessor line: " + line.strip())

    # A runtime value cannot be a case label.
    require("case g_wan_port_x" not in driver,
            "runtime WAN port is used as a case label")

    for symbol in ("g_wan_port_x", "g_mask_wan_port_x"):
        require(driver.count("static u32 %s" % symbol) == 1,
                "expected exactly one definition of " + symbol)
        require(len(re.findall(r"\b%s\b" % symbol, driver)) > 1,
                symbol + " is defined but never used")

    require("static u32 get_isolated_port_x(void)" in driver,
            "get_isolated_port_x is missing")
    require("static int change_wan_port_x(u32 port_x)" in driver,
            "change_wan_port_x is missing")
    require("change_wan_port_x(uint_param)" in dispatcher,
            "dispatcher does not call change_wan_port_x")
    require("MTK_ESW_IOCTL_WAN_PORT_X_SET" in uapi
            and "MTK_ESW_IOCTL_WAN_PORT_X_GET" in uapi,
            "new ioctl commands are missing from ioctl.h")
    require(dispatcher.count("MTK_ESW_IOCTL_WAN_PORT_X_GET") == 1,
            "read-back command is not dispatched exactly once")

    numbers = re.findall(r"#define\s+MTK_ESW_IOCTL_\w+\s+(\d+)\b", uapi)
    require(len(numbers) == len(set(numbers)),
            "duplicate MTK_ESW_IOCTL command numbers")

    for name, text in (("ioctl_mt762x.c", driver), ("ioctl.c", dispatcher)):
        stripped = strip_comments_and_strings(text)
        for opener, closer in (("{", "}"), ("(", ")"), ("[", "]")):
            require(stripped.count(opener) == stripped.count(closer),
                    "%s: unbalanced %s%s" % (name, opener, closer))

    if failures:
        print("FAIL runtime WAN-port override patch")
        for failure in failures:
            print("  " + failure)
        return 1

    print("PASS runtime WAN-port override patch structure")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
