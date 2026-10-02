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

# WireGuard client private/public keys are 44-character base64 strings.
# Keep the existing five ACL columns in order and append the public key.
path = trunk / "user/httpd/variables.c"
text = path.read_text()
pattern = re.compile(r"(struct variable variables_LANHostConfig_VPNSACLList\[\] = \{)(.*?)(\n\s*\};)", re.S)
matches = list(pattern.finditer(text))
if len(matches) != 1:
    raise SystemExit("Missing or ambiguous VPN server ACL schema")
match = matches[0]
body = match.group(2)
old_password = '{"vpns_pass_x", "32", NULL, FALSE}'
if body.count(old_password) != 1 or '"vpns_public_x"' in body:
    raise SystemExit("Unexpected VPN server ACL columns")
body = body.replace(old_password, '{"vpns_pass_x", "44", NULL, FALSE}')
terminator = "\t\t\t{0,0,0,0}"
if body.count(terminator) != 1:
    raise SystemExit("Missing VPN server ACL terminator")
body = body.replace(terminator, '#if defined(APP_AMNEZIAWG)\n'
                    '\t\t\t{"vpns_public_x", "44", NULL, FALSE},\n'
                    '#endif\n' + terminator)
text = text[:match.start(2)] + body + text[match.end(2):]
path.write_text(text)
print("Preserved VPN server ACL columns and 44-character key fields")

path = trunk / "user/shared/cflags.mk"
text = path.read_text()
if "APP_AMNEZIAWG" in text:
    raise SystemExit("Existing AmneziaWG build macro")
path.write_text(text.rstrip() + "\n\nifeq ($(CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG),y)\n"
                "CFLAGS += -DAPP_AMNEZIAWG\nendif\n")
print("Preserved", len(schema["defaults"]), "AmneziaWG NVRAM fields")
