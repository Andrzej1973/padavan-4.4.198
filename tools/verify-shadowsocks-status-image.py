#!/usr/bin/env python3
"""Check truthful Shadowsocks process-state text in final ROMFS."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("romfs", type=Path)
args = parser.parse_args()
root = args.romfs
page = (root / "www/Shadowsocks.asp").read_text(encoding="utf-8")
httpd = (root / "usr/sbin/httpd").read_bytes()
start = page.index("function fill_ss_status(status_code)")
end = page.index("function fill_dns2tcp_status(status_code)", start)
function = page[start:end]
required = (
    'typeof status_code === "number"',
    "Math.floor(status_code) === status_code",
    "status_code > 0",
    "status_code === 0",
    "WRSSProcessPresent",
    "WRSSProcessStopped",
    "WRSSProcessUnknown",
    "active ? 'success' : 'warning'",
)
missing = [item for item in required if item not in function]
if missing:
    raise SystemExit("Shadowsocks status function missing: " + ", ".join(missing))
if "WRSSProcessNote" not in page:
    raise SystemExit("Shadowsocks status scope note missing from image")
if "fill_ss_status(shadowsocks_status());" not in page or b"shadowsocks_status" not in httpd:
    raise SystemExit("Shadowsocks process status page/backend route missing from image")
for filename in ("EN.dict", "UK.dict", "RU.dict"):
    text = (root / "www" / filename).read_text(encoding="utf-8")
    for key in ("WRSSProcessPresent", "WRSSProcessStopped", "WRSSProcessUnknown", "WRSSProcessNote"):
        if not any(line.startswith(key + "=") and line[len(key) + 1:].strip() for line in text.splitlines()):
            raise SystemExit(f"Shadowsocks status label missing: {filename}:{key}")
print("PASS Shadowsocks status image: only a valid positive process count is green; functionality remains unverified")
