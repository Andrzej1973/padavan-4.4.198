#!/usr/bin/env python3
"""Check WPAD image packaging; this does not verify router HTTP behavior."""
import argparse
import json
from pathlib import Path
import os

parser = argparse.ArgumentParser()
parser.add_argument("trunk", type=Path)
parser.add_argument("report", type=Path)
args = parser.parse_args()
trunk = args.trunk
romfs = trunk / "romfs"
checks = {}

checks["effective_selector"] = "CONFIG_FIRMWARE_INCLUDE_WPAD=y" in (trunk / ".config").read_text()
for name in ("wpad.dat", "wpad.da", "proxy.pac"):
    link = romfs / "www" / name
    checks["link_" + name] = link.is_symlink() and os.readlink(link) == "/etc/storage/wpad.dat"
page = (romfs / "www/Advanced_DHCP_Content.asp").read_text()
checks["editor"] = 'name="scripts.wpad.dat"' in page
checks["capability_guard"] = "found_support_wpad() && !get_ap_mode()" in page
checks["login_guard"] = "inputCtrl(document.form['scripts.wpad.dat'], login_safe())" in page
server = (romfs / "usr/sbin/httpd").read_bytes()
checks["httpd_capability"] = b"found_support_wpad" in server
checks["httpd_mime"] = b"application/x-ns-proxy-autoconfig" in server
checks["httpd_field"] = b"scripts.wpad.dat" in server
storage = (romfs / "sbin/mtd_storage.sh").read_text()
checks["default_direct"] = 'function FindProxyForURL(url, host) { return "DIRECT"; }' in storage
checks["preserve_existing"] = '[ ! -e "$dir_storage/wpad.dat" ] && [ ! -L "$dir_storage/wpad.dat" ]' in storage
report = {"scope": "WPAD ROMFS packaging only; runtime unverified", "checks": checks}
args.report.write_text(json.dumps(report, indent=2) + "\n")
failed = [name for name, passed in checks.items() if not passed]
if failed:
    raise SystemExit("WPAD image checks failed: " + ", ".join(failed))
print("WPAD ROMFS checks passed; runtime remains unverified")
