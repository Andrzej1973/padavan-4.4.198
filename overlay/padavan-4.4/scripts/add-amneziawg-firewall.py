#!/usr/bin/env python3
"""Apply source AmneziaWG firewall branches to the pinned vendor kernel UI base."""
from pathlib import Path
import json
import sys
path = Path(sys.argv[1]) / "trunk/user/rc/firewall_ex.c"
text = path.read_text()
edits = json.loads(Path(__file__).with_name("amneziawg-firewall.json").read_text())
for edit in edits:
    if text.count(edit["old"]) != edit["count"]:
        raise SystemExit("Unexpected firewall anchor: " + edit["old"])
    text = text.replace(edit["old"], edit["new"])
path.write_text(text)
print("Applied", len(edits), "AmneziaWG firewall adaptations")
