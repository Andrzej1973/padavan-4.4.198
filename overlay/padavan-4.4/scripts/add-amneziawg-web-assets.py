#!/usr/bin/env python3
"""Install the source VPN pages' supporting web assets."""
from pathlib import Path
import shutil
import re
import sys
target = Path(sys.argv[1]) / "trunk/user/www/n56u_ribbon_fixed"
overlay = Path(__file__).resolve().parent.parent / "trunk/user/www/n56u_ribbon_fixed"
for name in ("jquery.multiSelectDropdown.js", "jquery.multiSelectDropdown.css",
             "qrcode.min.js"):
    if (target / name).exists():
        raise SystemExit("Unexpected existing VPN asset: " + name)
    shutil.copyfile(overlay / name, target / name)
general = target / "general.js"
text = general.read_text()
helper = Path(__file__).with_name("amneziawg-spoiler.js").read_text()
existing = re.findall(
    r"function spoiler_toggle\([^\n]*\)\s*\{.*?^\}", text, re.S | re.M)
if existing:
    normalize = lambda value: re.sub(r"\s+", "", value)
    if len(existing) != 1 or normalize(existing[0]) != normalize(helper):
        raise SystemExit("Existing spoiler helper differs from the source VPN helper")
    print("Reusing identical target spoiler helper")
else:
    general.write_text(text.rstrip() + "\n\n" + helper)
print("VPN dropdown, QR and spoiler assets installed")
