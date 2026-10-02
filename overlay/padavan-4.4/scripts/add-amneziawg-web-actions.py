#!/usr/bin/env python3
"""Port the source VPN page key/export actions into target HTTPD."""
from pathlib import Path
import sys
path = Path(sys.argv[1]) / "trunk/user/httpd/web_ex.c"
text = path.read_text()
anchor = '\telse if (!strcmp(value, " ClearLog "))'
if text.count(anchor) != 1 or '" wg_action "' in text:
    raise SystemExit("Unexpected HTTPD actions anchor")
actions = Path(__file__).with_name("amneziawg-web-actions.inc").read_text()
path.write_text(text.replace(anchor, actions + anchor))
print("AmneziaWG key generation and config export handlers installed")

text = path.read_text()
anchor = "static int ej_get_vpns_client(int eid, webs_t wp, int argc, char **argv)"
if text.count(anchor) != 1 or "leases_wireguard_server(void)" in text:
    raise SystemExit("Unexpected VPN client status handler")
leases = Path(__file__).with_name("amneziawg-leases.inc").read_text()
text = text.replace(anchor, leases + "\n" + anchor)
start = text.index(anchor)
file_anchor = '\tfp = fopen("/tmp/vpns.leases", "r");'
position = text.find(file_anchor, start)
if position < 0:
    raise SystemExit("Missing VPN client leases read")
text = text[:position] + '#if defined(APP_AMNEZIAWG)\n\tleases_wireguard_server();\n#endif\n\n' + text[position:]
path.write_text(text)
print("AmneziaWG server client status refresh installed")
