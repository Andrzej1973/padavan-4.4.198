#!/usr/bin/env python3
"""Install the source VPN pages' supporting web assets."""
from pathlib import Path
import shutil
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
if "function spoiler_toggle(" in text:
    raise SystemExit("Unexpected existing spoiler helper")
helper = Path(__file__).with_name("amneziawg-spoiler.js").read_text()
general.write_text(text.rstrip() + "\n\n" + helper)
print("VPN dropdown, QR and spoiler assets installed")
