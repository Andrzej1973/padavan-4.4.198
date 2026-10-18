#!/usr/bin/env python3
"""Verify SSH, Cron, discovery-service and watchdog module observers are packaged."""
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
    checks['cron_process_ui'] = all(marker in page for marker in (
        'wr_cron_process_status', 'wrCronRefresh', "output:'wr_cron_process_state'",
        'generation === wrCronGeneration', 'Date.now() - wrCronSampledAt >= 45000'))
    discovery_markers = (
        'wrLLTD_process_status', 'wrADSC_process_status',
        "output:'wr_' + service + '_process_state'", 'wrDiscoveryRefresh',
        'generation === wrDiscoveryGeneration[service]',
        'Date.now() - wrDiscoverySampledAt[service] >= 45000',
        '<% wr_lltd_process_state(); %>', '<% wr_adsc_process_state(); %>',
        '<#WRLLDTPresent#>', '<#WRADSCPresent#>')
    discovery_markers += (
        'wrWatchdog_process_status', '<% wr_watchdog_module_state(); %>',
        '<#WRWDGPresent#>', '<#WRWDGObservedNote#>')
    checks['discovery_process_ui'] = all(marker in page for marker in discovery_markers)
    checks['observation_expiry_ui'] = all(marker in page for marker in (
        'var wrSSHGeneration = 0', 'generation === wrSSHGeneration',
        '}, 45000)', "document.addEventListener('visibilitychange'",
        'Date.now() - wrSSHSampledAt >= 45000', 'Math.floor(state) === state'))
    ui_markers = ('wr_ssh_process_status', 'wrSSHRefresh',
                  "output:'wr_ssh_process_state'", 'document.hidden',
                  'window.setInterval(wrSSHRefresh, 30000)',
                  '<% wr_ssh_process_state(); %>',
                  'wr_ssh_observed_at', 'toLocaleTimeString()')
    checks['runtime_status_ui'] = all(marker in page for marker in ui_markers)
    httpd = (root / 'usr/sbin/httpd').read_bytes()
    checks['runtime_status_backend'] = b'wr_ssh_process_state' in httpd
    checks['cron_process_backend'] = b'wr_cron_process_state' in httpd
    checks['discovery_process_backend'] = all(
        marker in httpd for marker in (b'wr_lltd_process_state', b'wr_adsc_process_state',
                                       b'wr_watchdog_module_state'))
    status_keys = ('WRSSHObservedTitle', 'WRSSHOff', 'WRSSHPresent',
                   'WRSSHMissing', 'WRSSHUnknown', 'WRSSHStillPresent',
                   'WRSSHRefresh', 'WRSSHLastObservation',
                   'WRSSHNoObservation', 'WRSSHObservedNote')
    # ROMFS carries the merged dictionaries flat under www/ as *.dict.
    for locale, dictionary in (('EN', 'EN.dict'), ('UK', 'UK.dict'), ('RU', 'RU.dict')):
        translated = (root / 'www' / dictionary).read_text(encoding='utf-8')
        checks['runtime_status_locale_' + locale.lower()] = all(
            ('\n' + key + '=') in translated for key in status_keys)
        checks['cron_locale_' + locale.lower()] = all(
            ('\nWRCron' + suffix + '=') in translated for suffix in
            ('Off', 'Present', 'Missing', 'Unknown', 'StillPresent', 'Refresh', 'ObservedNote'))
        checks['discovery_locale_' + locale.lower()] = all(
            ('\n' + key + '=') in translated for key in (
                'WRLLTDObservedTitle', 'WRLLDTPresent', 'WRLLDTUnknown',
                'WRLLTDObservedNote', 'WRADSCObservedTitle', 'WRADSCPresent',
                'WRADSCUnknown', 'WRADSCObservedNote', 'WRWDGObservedTitle',
                'WRWDGPresent', 'WRWDGUnknown', 'WRWDGObservedNote'))
except (OSError, UnicodeError) as exc:
    checks['image_files_readable'] = False
    error = str(exc)
else:
    error = None
args.report.write_text(json.dumps({
    'scope': 'SSH and Cron process observers, LLTD/ASUS discovery process observers, and watchdog module-presence observer; protocol exchanges and hardware timer operation unverified',
    'checks': checks,
    'error': error,
}, indent=2) + '\n')
failed = [name for name, value in checks.items() if not value]
if failed:
    raise SystemExit('SSH image check failed: ' + ', '.join(failed))
print('SSH, Cron, LLTD/ASUS and watchdog module observers plus EN/UK/RU labels found in ROMFS; protocol exchanges and hardware timer operation remain unverified')
