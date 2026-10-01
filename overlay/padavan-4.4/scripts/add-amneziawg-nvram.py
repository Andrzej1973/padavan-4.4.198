#!/usr/bin/env python3
"""Preserve the original firmware's AmneziaWG NVRAM schema."""
import json
import re
import sys
from pathlib import Path

trunk = Path(sys.argv[1]) / "trunk"
schema = json.loads(Path(__file__).with_name("amneziawg-nvram.json").read_text())
def names(rows):
    return [re.search(r'"([^"]+)"', row).group(1) for row in rows]
if sorted(names(schema["defaults"])) != sorted(names(schema["variables"])):
    raise SystemExit("Defaults and HTTPD schemas differ")
if len(set(names(schema["defaults"]))) != len(schema["defaults"]):
    raise SystemExit("Duplicate source schema")
for relative, category in (("user/shared/defaults.c", "defaults"),
                           ("user/httpd/variables.c", "variables")):
    path = trunk / relative
    text = path.read_text()
    if any('"' + key + '"' in text for key in names(schema[category])):
        raise SystemExit("Existing AmneziaWG field in " + relative)
    for prefix in ("vpns", "vpnc"):
        pattern = re.compile(r'^.*\{' + r'\s*"' + prefix + r'_type".*$', re.M)
        matches = list(pattern.finditer(text))
        if len(matches) != 1:
            raise SystemExit("Missing or ambiguous insertion anchor: " + prefix)
        rows = [row for row in schema[category] if '"' + prefix + "_" in row]
        addition = "\n#if defined(APP_AMNEZIAWG)\n" + "\n".join(rows) + "\n#endif"
        match = matches[0]
        text = text[:match.end()] + addition + text[match.end():]
    path.write_text(text)
path = trunk / "user/shared/cflags.mk"
text = path.read_text()
if "APP_AMNEZIAWG" in text:
    raise SystemExit("Existing AmneziaWG build macro")
path.write_text(text.rstrip() + "\n\nifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)\n"
                "CFLAGS += -DAPP_AMNEZIAWG\nendif\n")
print("Preserved", len(schema["defaults"]), "AmneziaWG NVRAM fields")
