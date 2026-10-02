#!/usr/bin/env python3
"""Append missing source VPN labels without replacing existing translations."""
import json
from pathlib import Path
import sys

root = Path(sys.argv[1]) / "trunk/user/www/n56u_ribbon_fixed"
data = json.loads(Path(__file__).with_name("amneziawg-vpn-labels.json").read_text(encoding="utf-8"))
for language, entries in data["languages"].items():
    path = root / ("EN.footer" if language == "EN" else language + ".dict")
    text = path.read_text(encoding="utf-8")
    present = {line.split("=", 1)[0] for line in text.splitlines() if "=" in line}
    additions = []
    for entry in entries:
        key, value = entry.split("=", 1)
        if key not in present:
            additions.append(entry)
            present.add(key)
    missing = set(data["required_keys"]) - present
    if missing:
        raise SystemExit(language + " missing VPN labels: " + ", ".join(sorted(missing)))
    if additions:
        path.write_text(text.rstrip() + "\n" + "\n".join(additions) + "\n", encoding="utf-8")
    print(language + ": all VPN labels present; added " + str(len(additions)))
