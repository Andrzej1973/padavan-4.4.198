#!/usr/bin/env python3
"""Install pinned original VPN pages after their dependencies are adapted."""
from pathlib import Path
import shutil
import sys
root = Path(sys.argv[1]) / "trunk/user"
overlay = Path(__file__).resolve().parent.parent / "trunk/user/www/n56u_ribbon_fixed"
webex = (root / "httpd/web_ex.c").read_text()
variables = (root / "httpd/variables.c").read_text()
for marker in ('found_app_awg', '" wg_action "', '" ExportWGConf "', 'leases_wireguard_server(void)'):
    if marker not in webex:
        raise SystemExit("Missing VPN page handler: " + marker)
for marker in ('"vpns_public_x"', '"scripts.vpnc_remote_network.list"', '"scripts.vpnc_exclude_network.list"', '"scripts.vpnc_post_script.sh"'):
    if marker not in variables:
        raise SystemExit("Missing VPN page field: " + marker)
target = root / "www/n56u_ribbon_fixed"
for name in ("jquery.multiSelectDropdown.js", "qrcode.min.js"):
    if not (target / name).is_file():
        raise SystemExit("Missing VPN page asset: " + name)
json_source = root / "amneziawg/amneziawg.json"
if not json_source.is_file():
    raise SystemExit("Missing AmneziaWG parameter defaults")
shutil.copyfile(json_source, target / "amneziawg.json")
for name in ("vpncli.asp", "vpnsrv.asp"):
    if not (target / name).is_file():
        raise SystemExit("Missing native VPN page: " + name)
    shutil.copyfile(overlay / name, target / name)
print("Pinned source VPN client/server pages installed")

# These shared pages also serve native PPTP/L2TP and AmneziaWG.
makefile = root / "www/Makefile"
text = makefile.read_text()
removal = "ifneq ($(CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_SERVER),y)\n\trm -f $(INSTALLDIR)/www/vpnsrv.asp\nendif\nifneq ($(CONFIG_FIRMWARE_INCLUDE_SOFTETHERVPN_CLIENT),y)\n\trm -f $(INSTALLDIR)/www/vpn_clients.asp\n\trm -f $(INSTALLDIR)/www/vpncli.asp\nendif"
if text.count(removal) != 1:
    raise SystemExit("Unexpected shared VPN page removal rules")
makefile.write_text(text.replace(removal, "# Shared VPN pages retained for native VPN and AmneziaWG"))
print("Shared VPN pages retained independently of SoftEther")
