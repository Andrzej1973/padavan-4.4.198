#!/usr/bin/env python3
"""Preserve source DDNS SSL defaults in vendor 4.4."""
from pathlib import Path
import re
import sys
path = Path(sys.argv[1]) / "trunk/user/shared/defaults.c"
text = path.read_text()
for key in ("ddns_ssl", "ddns2_ssl"):
    pattern = re.compile(r'(\{\s*"' + key + r'"\s*,\s*")0("\s*\})')
    text, count = pattern.subn(lambda match: match.group(1) + "1" + match.group(2), text)
    if count != 1:
        raise SystemExit("Unexpected DDNS default: " + key)
path.write_text(text)
print("Preserved source SSL defaults for both DDNS profiles")
