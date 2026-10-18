#!/usr/bin/env python3
"""Verify discovery-service and KMS status controls in final ROMFS."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('romfs', type=Path)
args = parser.parse_args()
root = args.romfs
page = (root / 'www/Advanced_Services_Content.asp').read_text(encoding='utf-8')
httpd = (root / 'usr/sbin/httpd').read_bytes()

required_page = (
    'id="row_vlmcsd"', 'id="wrVlmcsd_status_row"',
    'id="wrVlmcsd_process_status"', 'function wrVlmcsdRefresh()',
    'onclick="wrVlmcsdRefresh()"',
    "wrDiscoveryRender('vlmcsd', <% wr_vlmcsd_process_state(); %>);",
    'wr_vlmcsd_process_state', 'wrVlmcsdRefresh();',
    'wrVlmcsdRefresh();wrWatchdogRefresh();},30000)', 'document.hidden',
    '}, 45000)', 'WRVLMCSNoObservation',
)
missing = [marker for marker in required_page if marker not in page]
if missing:
    raise SystemExit('Discovery/KMS status page markers missing: ' + ', '.join(missing))
backend_markers = (b'wr_vlmcsd_process_state', b'vlmcsd_enable', b'/usr/bin/vlmcsd')
if any(marker not in httpd for marker in backend_markers):
    raise SystemExit('KMS status handler or exact process mapping is missing from final httpd')

for filename in ('EN.dict', 'UK.dict', 'RU.dict'):
    text = (root / 'www' / filename).read_text(encoding='utf-8')
    for key in ('WRVLMCSObservedTitle', 'WRVLMCSOff', 'WRVLMCSRunning',
                'WRVLMCSMissing', 'WRVLMCSUnknown', 'WRVLMCSStillRunning',
                'WRVLMCSRefresh', 'WRVLMCSLastObservation',
                'WRVLMCSNoObservation', 'WRVLMCSObservedNote'):
        if not any(line.startswith(key + '=') and line[len(key) + 1:].strip()
                   for line in text.splitlines()):
            raise SystemExit(f'KMS status translation missing: {filename}:{key}')

print('PASS final ROMFS KMS status: saved setting compared with vlmcsd process presence; activation result remains unverified')
