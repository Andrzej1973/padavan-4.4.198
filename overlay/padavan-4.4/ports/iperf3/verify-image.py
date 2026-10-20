#!/usr/bin/env python3
"""Verify iPerf3 status UI and handler are present in the selected image."""
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
    checks['selector'] = 'CONFIG_FIRMWARE_INCLUDE_IPERF3=y' in config
    page = (root / 'www/Advanced_Services_Content.asp').read_text()
    checks['observation_expiry_ui'] = all(marker in page for marker in (
        'var wrIperf3Generation = 0', 'generation === wrIperf3Generation',
        '}, 45000)', "document.addEventListener('visibilitychange'",
        'Date.now() - wrIperf3SampledAt >= 45000', 'Math.floor(state) === state'))
    ui_markers = ('wr_iperf3_process_status', 'wrIperf3Refresh',
                  "output:'wr_iperf3_process_state'", 'document.hidden',
                  'window.setInterval(wrIperf3Refresh, 30000)',
                  '<% wr_iperf3_process_state(); %>',
                  'wr_iperf3_observed_at', 'toLocaleTimeString()')
    checks['runtime_status_ui'] = all(marker in page for marker in ui_markers)
    test_markers = (
        'id="wr_iperf3_test_help_row"',
        'iperf3 -c <span id="wr_iperf3_lan_address"></span> -t 10',
        "address.textContent = lan_ipaddr ||",
        "showhide_div('wr_iperf3_test_help_row', 0)",
        'WRIperf3TestInstructions', 'WRIperf3TestLimits',
    )
    checks['bounded_lan_test_instructions'] = all(marker in page for marker in test_markers)
    httpd = (root / 'usr/sbin/httpd').read_bytes()
    checks['runtime_status_backend'] = b'wr_iperf3_process_state' in httpd
    status_keys = ('WRIperf3ObservedTitle', 'WRIperf3Off', 'WRIperf3Present',
                   'WRIperf3Missing', 'WRIperf3Unknown', 'WRIperf3StillPresent',
                   'WRIperf3Refresh', 'WRIperf3LastObservation',
                   'WRIperf3NoObservation', 'WRIperf3ObservedNote',
                   'WRIperf3TestTitle', 'WRIperf3TestInstructions',
                   'WRIperf3TestLimits', 'WRIperf3LanAddressUnknown')
    # ROMFS carries the merged dictionaries flat under www/ as *.dict.
    for locale, dictionary in (('EN', 'EN.dict'), ('UK', 'UK.dict'), ('RU', 'RU.dict')):
        translated = (root / 'www' / dictionary).read_text(encoding='utf-8')
        checks['runtime_status_locale_' + locale.lower()] = all(
            ('\n' + key + '=') in translated for key in status_keys)
except (OSError, UnicodeError) as exc:
    checks['image_files_readable'] = False
    error = str(exc)
else:
    error = None
args.report.write_text(json.dumps({
    'scope': 'iPerf3 status UI, HTTP handler and bounded LAN client-test instructions; actual client test and throughput remain unverified',
    'checks': checks,
    'error': error,
}, indent=2) + '\n')
failed = [name for name, value in checks.items() if not value]
if failed:
    raise SystemExit('iPerf3 image check failed: ' + ', '.join(failed))
print('iPerf3 status UI, HTTP handler and EN/UK/RU labels found in ROMFS; client test remains unverified')
