#!/usr/bin/env python3
"""Structural checks for the rc wiring of the WAN port override.

Not a compiler: the full MIPS cross-compile is the build evidence. These
invariants catch a missing integration step and a wiring that would apply the
selection after the bridge rebuild that consumes it.
"""
import argparse
import re
from pathlib import Path


def strip_comments_and_strings(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", " ", text, flags=re.S)
    text = re.sub(r"//[^\n]*", " ", text)
    return re.sub(r'"(?:\\.|[^"\\])*"', '""', text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="applied Padavan tree root")
    args = parser.parse_args()

    rc = args.tree / "trunk/user/rc"
    header = (rc / "switch.h").read_text(encoding="utf-8")
    adapter = (rc / "switch_mtk_esw.c").read_text(encoding="utf-8")
    lan = (rc / "net_lan.c").read_text(encoding="utf-8")
    wan = (rc / "net_wan.c").read_text(encoding="utf-8")

    failures = []

    def require(condition, message):
        if not condition:
            failures.append(message)

    require("int phy_wan_port_x_set(unsigned int port_x);" in header,
            "switch.h does not declare phy_wan_port_x_set")
    require(adapter.count("MTK_ESW_IOCTL_WAN_PORT_X_SET") >= 2,
            "switch_mtk_esw.c does not issue the override command")
    require("int phy_wan_port_x_set(unsigned int port_x)" in adapter,
            "phy_wan_port_x_set is not implemented")
    require(adapter.count("MTK_ESW_IOCTL_WAN_PORT_X_GET") == 2,
            "the switch tool does not read the effective port back")
    require('"   66 [PORT]        Move the WAN role to an external port' in adapter
            and '"   67               Show the effective WAN port' in adapter,
            "the switch tool usage text does not document the new commands")

    require("int\nwan_switch_port(void)" in lan,
            "wan_switch_port is missing")
    require(lan.count("phy_wan_port_x_set(wan_switch_port());") == 1,
            "the selected socket is not applied exactly once")
    require(lan.count("is_vlan_vid_valid(nvram_get_int(rule_key[rule_id]))") == 1,
            "tagged-VLAN refusal is missing")
    require('nvram_get_int("wan_src_phy")' in lan,
            "the selection no longer comes from wan_src_phy")
    require(lan.count("return SWAPI_PORT_WAN;") >= 3,
            "the helper no longer falls back to the board socket")

    # The override must be applied before the bridge rebuild that consumes it.
    apply_at = lan.find("phy_wan_port_x_set(wan_switch_port());")
    rebuild_at = lan.find("\tphy_bridge_mode(bridge_mode, bwan_isolation);")
    require(apply_at != -1 and rebuild_at != -1 and apply_at < rebuild_at,
            "the override is applied after the bridge rebuild")

    # Link monitoring keeps using the same socket.
    require('nvram_get_int("wan_src_phy")' in wan,
            "net_wan.c no longer follows wan_src_phy for link monitoring")

    for name, text in (("net_lan.c", lan), ("switch_mtk_esw.c", adapter)):
        stripped = strip_comments_and_strings(text)
        for opener, closer in (("{", "}"), ("(", ")"), ("[", "]")):
            require(stripped.count(opener) == stripped.count(closer),
                    "%s: unbalanced %s%s" % (name, opener, closer))

    if failures:
        print("FAIL rc wiring for the WAN port override")
        for failure in failures:
            print("  " + failure)
        return 1

    print("PASS rc wiring for the WAN port override")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
