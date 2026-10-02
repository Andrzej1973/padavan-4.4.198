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
