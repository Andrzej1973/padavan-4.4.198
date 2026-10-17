#!/usr/bin/env python3
"""Start and stop the independent VPN profile service from rc.

The service is default-off: it reads `wrvpn_enabled` and `wrvpn_protect` from
nvram and does nothing when the list is empty. Starting it at boot and stopping
it with the other services keeps activation in one place, and the service
itself refuses profile addresses unless the protected prefixes are set.
"""
import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tree", type=Path, help="Padavan tree root")
    args = parser.parse_args()
    services = args.tree / "trunk/user/rc/services.c"
    text = services.read_text(encoding="utf-8")

    if "wr-vpn-profiles-service" in text:
        raise RuntimeError("VPN profile service already integrated")

    start_anchor = (
        '\tsystem("/usr/bin/iappd.sh test");\n'
        "\treturn 0;\n"
        "}\n"
    )
    start_addition = (
        "\t/* Independent VPN profiles: default-off, driven by nvram. */\n"
        "\tif (!is_ap_mode)\n"
        '\t\tdoSystem("/usr/sbin/wr-vpn-profiles-service start");\n'
    )
    if text.count(start_anchor) != 1:
        raise RuntimeError("start_services_once anchor changed")
    text = text.replace(start_anchor, start_addition + start_anchor, 1)

    stop_anchor = "void\nstop_services(int stopall)\n{\n"
    stop_addition = (
        "\t/* Scoped teardown: rule, routes and addresses before other services. */\n"
        '\tdoSystem("/usr/sbin/wr-vpn-profiles-service stop");\n'
    )
    if text.count(stop_anchor) != 1:
        raise RuntimeError("stop_services anchor changed")
    text = text.replace(stop_anchor, stop_anchor + stop_addition, 1)

    services.write_text(text, encoding="utf-8", newline="\n")
    print("PASS integrated the VPN profile service into rc start and stop")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
