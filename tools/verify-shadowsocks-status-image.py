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
start = page.index("function wrSSProcessRender(kind, state)")
end = page.index("function fill_ss_external_status()", start)
function = page[start:end]
function_required = ("state === 1", "active ? 'success' : 'warning'",
                     "typeof state === 'number'", "state < labels.length")
missing_function = [item for item in function_required if item not in function]
if missing_function:
    raise SystemExit("Shadowsocks state renderer missing: " + ", ".join(missing_function))
required = (
    "wr_ss_client_process_state",
    "window.setInterval(wrSSProcessRefreshAll, 30000)",
    "document.hidden",
    "}, 45000)",
    "onclick=\"wrSSProcessRefresh('redir')\"",
    "onclick=\"wrSSProcessRefresh('local')\"",
    'wr_ss_client_process_state("redir")',
    'wr_ss_client_process_state("local")',
)
missing = [item for item in required if item not in page]
if missing:
    raise SystemExit("Shadowsocks status image missing: " + ", ".join(missing))
if "WRSSProcessNote" not in page:
    raise SystemExit("Shadowsocks status scope note missing from image")
backend_markers = (b"wr_ss_client_process_state", b"ss-redir", b"ss-local", b"ss_enable", b"socks5_enable")
if any(marker not in httpd for marker in backend_markers):
    raise SystemExit("Shadowsocks process status page/backend route missing from image")
for filename in ("EN.dict", "UK.dict", "RU.dict"):
    text = (root / "www" / filename).read_text(encoding="utf-8")
    for key in ("WRSSRedirTitle", "WRSSLocalTitle", "WRSSOff", "WRSSPresent",
                "WRSSMissing", "WRSSUnknown", "WRSSStillPresent", "WRSSRefresh",
                "WRSSObservedAt", "WRSSNoObservation", "WRSSProcessNote"):
        if not any(line.startswith(key + "=") and line[len(key) + 1:].strip() for line in text.splitlines()):
            raise SystemExit(f"Shadowsocks status label missing: {filename}:{key}")
print("PASS Shadowsocks image: requested state is compared with exact ss-redir/ss-local processes; connectivity remains unverified")
