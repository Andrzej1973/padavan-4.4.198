#!/usr/bin/env python3
"""Verify SSH status UI and handler are present in the selected image."""
import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('trunk', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
root = args.trunk / 'romfs'
checks = {}
try:
    config = (args.trunk / '.config').read_text().splitlines()
    checks['ssh_capability'] = any(
        name in config for name in ('CONFIG_FIRMWARE_INCLUDE_DROPBEAR=y',
                                    'CONFIG_FIRMWARE_INCLUDE_OPENSSH=y'))
    page = (root / 'www/Advanced_Services_Content.asp').read_text()
    ui_markers = ('wr_ssh_process_status', 'wrSSHRefresh',
                  "output:'wr_ssh_process_state'", 'document.hidden',
                  'window.setInterval(wrSSHRefresh, 30000)',
                  '<% wr_ssh_process_state(); %>',
                  'wr_ssh_observed_at', 'toLocaleTimeString()')
    checks['runtime_status_ui'] = all(marker in page for marker in ui_markers)
    httpd = (root / 'usr/sbin/httpd').read_bytes()
    checks['runtime_status_backend'] = b'wr_ssh_process_state' in httpd
    status_keys = ('WRSSHObservedTitle', 'WRSSHOff', 'WRSSHPresent',
                   'WRSSHMissing', 'WRSSHUnknown', 'WRSSHStillPresent',
                   'WRSSHRefresh', 'WRSSHLastObservation',
                   'WRSSHNoObservation', 'WRSSHObservedNote')
    for locale, dictionary in (('EN', 'EN.footer'), ('UK', 'UK.dict'), ('RU', 'RU.dict')):
        translated = (root / 'www/dict' / dictionary).read_text(encoding='utf-8')
        checks['runtime_status_locale_' + locale.lower()] = all(
            ('\n' + key + '=') in translated for key in status_keys)
except (OSError, UnicodeError) as exc:
    checks['image_files_readable'] = False
    error = str(exc)
else:
    error = None
args.report.write_text(json.dumps({
    'scope': 'SSH status UI and HTTP handler packaging; connection/authentication unverified',
    'checks': checks,
    'error': error,
}, indent=2) + '\n')
failed = [name for name, value in checks.items() if not value]
if failed:
    raise SystemExit('SSH image check failed: ' + ', '.join(failed))
print('SSH status UI, HTTP handler and EN/UK/RU labels found in ROMFS; connection/authentication remain unverified')
