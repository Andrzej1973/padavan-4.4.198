#!/usr/bin/env python3
"""Let rc move the WAN role to the socket named by wan_src_phy.

Companion to overlay/padavan-4.4/patches/wan-port-runtime.diff, which adds the
runtime override to the switch driver. In the pinned base tree wan_src_phy only
selected the socket whose link reported WAN up, and the web UI already exposes it
as the WAN source port next to wan_stb_x. This script wires that existing
selection to the driver, so a damaged original WAN socket can be replaced by
LAN1-LAN4:

  * the selected socket becomes the WAN socket,
  * the board's original WAN socket stays isolated in the driver,
  * a socket that already carries a tag-based VLAN rule is refused instead of
    being silently taken over, and
  * zero (the default) keeps the previous behaviour exactly.
"""
import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="Padavan tree root")
    args = parser.parse_args()
    root = args.tree / "trunk/user/rc"

    edits = {}

    def change(name, anchor, addition, after=False):
        target = root / name
        text = edits.get(target, target.read_text(encoding="utf-8"))
        if text.count(anchor) != 1:
            raise RuntimeError("Unexpected anchor in " + name)
        replacement = anchor + addition if after else addition + anchor
        edits[target] = text.replace(anchor, replacement, 1)

    # 1. Switch abstraction: expose the new driver command.
    change("switch.h",
           "int phy_bridge_mode(unsigned int bridge_mode, int isolated_mode);\n",
           "int phy_wan_port_x_set(unsigned int port_x);\n",
           after=True)

    change("switch_mtk_esw.c",
           "int phy_bridge_mode(unsigned int bridge_mode, int isolated_mode)\n"
           "{\n"
           "\treturn mtk_esw_ioctl(MTK_ESW_IOCTL_BRIDGE_MODE, isolated_mode, &bridge_mode);\n"
           "}\n",
           "\nint phy_wan_port_x_set(unsigned int port_x)\n"
           "{\n"
           "\tunsigned int value = port_x;\n"
           "\treturn mtk_esw_ioctl(MTK_ESW_IOCTL_WAN_PORT_X_SET, port_x, &value);\n"
           "}\n",
           after=True)

    # 2. Resolve the requested socket, refusing sockets that carry VLAN rules.
    change("net_lan.c",
           "void\nswitch_config_vlan(int first_call)\n{\n",
           "/*\n"
           " * External socket that must carry the WAN role. Zero is the board\n"
           " * socket, so an unset or zero value keeps the previous behaviour;\n"
           " * LAN1..LAN4 let a damaged original socket be replaced. A socket that\n"
           " * already carries a tag-based VLAN rule is refused instead of being\n"
           " * silently taken over.\n"
           " */\n"
           "int\n"
           "wan_switch_port(void)\n"
           "{\n"
           "\tstatic const char *const rule_key[SWAPI_VLAN_RULE_NUM] = {\n"
           "\t\t\"vlan_vid_cpu\", \"vlan_vid_iptv\", \"vlan_vid_lan1\",\n"
           "\t\t\"vlan_vid_lan2\", \"vlan_vid_lan3\", \"vlan_vid_lan4\"\n"
           "\t};\n"
           "\tint port = nvram_get_int(\"wan_src_phy\");\n"
           "\tint rule_id;\n"
           "\n"
           "\tif (port <= SWAPI_PORT_WAN || port > SWAPI_PORT_LAN4)\n"
           "\t\treturn SWAPI_PORT_WAN;\n"
           "\n"
           "\tif (!nvram_match(\"vlan_filter\", \"1\"))\n"
           "\t\treturn port;\n"
           "\n"
           "\trule_id = SWAPI_VLAN_RULE_WAN_LAN1 + (port - SWAPI_PORT_LAN1);\n"
           "\tif (rule_id > SWAPI_VLAN_RULE_WAN_LAN4)\n"
           "\t\treturn SWAPI_PORT_WAN;\n"
           "\n"
           "\tif (is_vlan_vid_valid(nvram_get_int(rule_key[rule_id])))\n"
           "\t\treturn SWAPI_PORT_WAN;\n"
           "\n"
           "\treturn port;\n"
           "}\n"
           "\n")

    # 3. Apply it before the bridge rebuild, so every mask and VLAN entry
    #    follows the selected socket.
    change("net_lan.c",
           "\tphy_bridge_mode(bridge_mode, bwan_isolation);\n",
           "\t/* Move the WAN role before the rebuild that consumes it. */\n"
           "\tphy_wan_port_x_set(wan_switch_port());\n"
           "\n")

    # 4. Let the shipped switch tool change the socket and read back the
    #    effective one, so acceptance can be verified from a shell.
    change("switch_mtk_esw.c",
           "\t\"   64 [MASK] [DATA] Create VLAN entry\\n\"\n",
           "\t\"   66 [PORT]        Move the WAN role to an external port\\n\"\n"
           "\t\"   67               Show the effective WAN port\\n\"\n",
           after=True)

    change("switch_mtk_esw.c",
           "static int show_vlan_pvid_wan(void)\n"
           "{\n"
           "\tint retVal;\n"
           "\tunsigned int arg = 2;\n"
           "\n"
           "\tretVal = mtk_esw_ioctl(MTK_ESW_IOCTL_VLAN_PVID_WAN_GET, 0, &arg);\n"
           "\tif (retVal != 0)\n"
           "\t\targ = 2;\n"
           "\n"
           "\tprintf(\"%d\\n\", arg);\n"
           "\n"
           "\treturn retVal;\n"
           "}\n",
           "\nstatic int show_wan_port_x(void)\n"
           "{\n"
           "\tint retVal;\n"
           "\tunsigned int port_x = 0;\n"
           "\n"
           "\tretVal = mtk_esw_ioctl(MTK_ESW_IOCTL_WAN_PORT_X_GET, 0, &port_x);\n"
           "\tif (retVal != 0)\n"
           "\t\treturn retVal;\n"
           "\n"
           "\tprintf(\"%u\\n\", port_x);\n"
           "\n"
           "\treturn retVal;\n"
           "}\n",
           after=True)

    change("switch_mtk_esw.c",
           "\tcase MTK_ESW_IOCTL_VLAN_PVID_WAN_GET:\n"
           "\t\treturn show_vlan_pvid_wan();\n",
           "\n"
           "\tcase MTK_ESW_IOCTL_WAN_PORT_X_SET:\n"
           "\t\tif (mtk_esw_ioctl(MTK_ESW_IOCTL_WAN_PORT_X_SET, arg, &arg) != 0)\n"
           "\t\t\treturn 1;\n"
           "\t\treturn show_wan_port_x();\n"
           "\n"
           "\tcase MTK_ESW_IOCTL_WAN_PORT_X_GET:\n"
           "\t\treturn show_wan_port_x();\n",
           after=True)

    # WAN is a logical role in the patched driver. Reading the requested LAN
    # directly is wrong when a VLAN conflict caused fallback to the board port.
    change("net_wan.c",
           '\t\twan_src_phy = nvram_get_int("wan_src_phy");\n',
           '#if defined(BOARD_WR1200JS)\n'
           '\t\twan_src_phy = SWAPI_PORT_WAN; /* driver resolves effective WAN */\n'
           '#else\n', after=False)
    change("net_wan.c",
           '\t\twan_src_phy = nvram_get_int("wan_src_phy");\n',
           '#endif\n', after=True)

    for target, text in edits.items():
        target.write_text(text, encoding="utf-8", newline="\n")

    print("PASS wired rc to the runtime WAN port override")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
