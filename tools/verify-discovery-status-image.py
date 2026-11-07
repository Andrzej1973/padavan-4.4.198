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
    'id="div_vlmcsd"', 'id="wrVlmcsd_status_row"',
    'id="wrVlmcsd_process_status"', 'function wrVlmcsdRefresh()',
    'onclick="wrVlmcsdRefresh()"',
    "wrDiscoveryRender('vlmcsd', <% wr_vlmcsd_process_state(); %>);",
    'id="wrWatchdog_status_row"', 'id="wrWatchdog_process_status"',
    'function wrWatchdogRefresh()', 'onclick="wrWatchdogRefresh()"',
    "wrDiscoveryRender('watchdog', <% wr_watchdog_module_state(); %>);",
    'wr_vlmcsd_process_state', 'wrVlmcsdRefresh();',
    'wrVlmcsdRefresh();wrWatchdogRefresh();},30000)', 'document.hidden',
    '}, 45000)', 'WRVLMCSNoObservation',
)
missing = [marker for marker in required_page if marker not in page]
if missing:
    raise SystemExit('Discovery/KMS status page markers missing: ' + ', '.join(missing))
backend_markers = (
    b'wr_vlmcsd_process_state', b'vlmcsd_enable', b'/usr/bin/vlmcsd',
    b'wr_watchdog_module_state', b'watchdog_cpu', b'/sys/module/rt_timer_wdg',
)
if any(marker not in httpd for marker in backend_markers):
    raise SystemExit('KMS/watchdog status handler or exact provider mapping is missing from final httpd')

for filename in ('EN.dict', 'UK.dict', 'RU.dict'):
    text = (root / 'www' / filename).read_text(encoding='utf-8')
    for key in ('WRVLMCSObservedTitle', 'WRVLMCSOff', 'WRVLMCSRunning',
                'WRVLMCSMissing', 'WRVLMCSUnknown', 'WRVLMCSStillRunning',
                'WRVLMCSRefresh', 'WRVLMCSLastObservation',
                'WRVLMCSNoObservation', 'WRVLMCSObservedNote',
                'WRWDGObservedTitle', 'WRWDGOff', 'WRWDGPresent',
                'WRWDGMissing', 'WRWDGUnknown', 'WRWDGStillPresent',
                'WRWDGRefresh', 'WRWDGLastObservation',
                'WRWDGNoObservation', 'WRWDGObservedNote'):
        if not any(line.startswith(key + '=') and line[len(key) + 1:].strip()
                   for line in text.splitlines()):
            raise SystemExit(f'KMS/watchdog status translation missing: {filename}:{key}')
    note = next(line.split('=', 1)[1] for line in text.splitlines()
                if line.startswith('WRWDGObservedNote='))
    if not all(term in note for term in ('watchdog_cpu', 'rt_timer_wdg', 'MT7621')):
        raise SystemExit(f'Watchdog note is incomplete or untranslated: {filename}:WRWDGObservedNote')

print('PASS final ROMFS KMS/watchdog status rows, handlers and EN/UK/RU help; activation and hardware-timer operation remain unverified')
