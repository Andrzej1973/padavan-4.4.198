#!/usr/bin/env python3
"""Trust WebUI management from our WireGuard interfaces."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("tree", type=Path, help="Padavan tree root")
args = parser.parse_args()

path = args.tree / "trunk/user/httpd/httpd.c"
text = path.read_text(encoding="utf-8")
anchor = """static int
is_safe_ifname(const char *ifname)
{
\tif (strcmp(ifname, IFNAME_BR) == 0)
\t\treturn 1;
"""
if text.count(anchor) != 1 or "wg-management-trust" in text:
    raise RuntimeError("httpd safe-interface anchor changed")
addition = """\t/* wg-management-trust: clients routed through our WireGuard
\t * interfaces are as trusted as the LAN for WebUI management (legacy
\t * wg0/wg1 and independent profile interfaces). */
\tif (strncmp(ifname, "wg", 2) == 0 || strncmp(ifname, "wrvpn", 5) == 0)
\t\treturn 1;
"""
text = text.replace(anchor, anchor + addition, 1)
path.write_text(text, encoding="utf-8", newline="\n")
print("PASS WebUI management trusted over WireGuard interfaces")
