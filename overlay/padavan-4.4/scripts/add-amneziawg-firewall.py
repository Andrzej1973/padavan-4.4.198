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

# Preserve the NVRAM key used by the user's original firmware, including
# the checkbox/radio IDs in the existing DHCP page.
user = Path(sys.argv[1]) / "trunk/user"
renamed = []
for candidate in user.rglob("*"):
    if not candidate.is_file() or candidate.suffix not in {
        ".c", ".h", ".asp", ".js", ".mk", ".config"
    }:
        continue
    data = candidate.read_bytes()
    if b"redirect_all_dns" in data:
        candidate.write_bytes(data.replace(b"redirect_all_dns", b"force_redirect_dns"))
        renamed.append(candidate.relative_to(user).as_posix())
if "shared/defaults.c" not in renamed or "httpd/variables.c" not in renamed:
    raise SystemExit("DNS NVRAM schema anchors missing")
if "www/n56u_ribbon_fixed/Advanced_DHCP_Content.asp" not in renamed:
    raise SystemExit("DNS UI anchor missing")
print("Preserved source force_redirect_dns key in:", ", ".join(renamed))
