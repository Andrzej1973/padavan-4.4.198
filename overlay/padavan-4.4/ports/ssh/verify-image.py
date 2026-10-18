#!/usr/bin/env python3
"""Verify SSH, Cron, discovery-service and watchdog module observers are packaged."""
import argparse
import json
from pathlib import Path
import re

parser = argparse.ArgumentParser()
parser.add_argument('trunk', type=Path)
parser.add_argument('report', type=Path)
parser.add_argument('--source-page', type=Path,
                    help='pre-ROMFS source page for locating lost WebUI markers')
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
    discovery_markers = {
        'lltd_status_element': 'wrLLTD_process_status',
        'adsc_status_element': 'wrADSC_process_status',
        'refresh_output_mapping': "vlmcsd:'wr_vlmcsd_process_state'",
        'refresh_endpoint_selection': 'data:{output:outputs[service]}',
        'refresh_function': 'wrDiscoveryRefresh',
        'stale_response_guard': 'generation === wrDiscoveryGeneration[service]',
        'observation_expiry': 'Date.now() - wrDiscoverySampledAt[service] >= 45000',
        'lltd_http_handler': '<% wr_lltd_process_state(); %>',
        'adsc_http_handler': '<% wr_adsc_process_state(); %>',
        'vlmcsd_status_element': 'wrVlmcsd_process_status',
        'vlmcsd_http_handler': '<% wr_vlmcsd_process_state(); %>',
        'vlmcsd_off_translation': '<#WRVLMCSOff#>',
        'vlmcsd_present_translation': '<#WRVLMCSRunning#>',
        'vlmcsd_missing_translation': '<#WRVLMCSMissing#>',
        'vlmcsd_unknown_translation': '<#WRVLMCSUnknown#>',
        'vlmcsd_still_running_translation': '<#WRVLMCSStillRunning#>',
        'vlmcsd_refresh_translation': '<#WRVLMCSRefresh#>',
        'vlmcsd_note_translation': '<#WRVLMCSObservedNote#>',
        'lltd_present_translation': '<#WRLLDTPresent#>',
        'adsc_present_translation': '<#WRADSCPresent#>',
        'watchdog_status_element': 'wrWatchdog_process_status',
        'watchdog_http_handler': '<% wr_watchdog_module_state(); %>',
        'watchdog_off_translation': '<#WRWDGOff#>',
        'watchdog_present_translation': '<#WRWDGPresent#>',
        'watchdog_missing_translation': '<#WRWDGMissing#>',
        'watchdog_unknown_translation': '<#WRWDGUnknown#>',
        'watchdog_still_present_translation': '<#WRWDGStillPresent#>',
        'watchdog_refresh_translation': '<#WRWDGRefresh#>',
        'watchdog_note_translation': '<#WRWDGObservedNote#>',
    }
    for name, marker in discovery_markers.items():
        checks['discovery_process_ui_' + name] = marker in page
    checks['discovery_process_ui'] = all(
        checks['discovery_process_ui_' + name] for name in discovery_markers)
    if args.source_page:
        source_page = args.source_page.read_text(encoding='utf-8')
        for name, marker in discovery_markers.items():
            checks['discovery_source_ui_' + name] = marker in source_page
        checks['discovery_source_ui'] = all(
            checks['discovery_source_ui_' + name] for name in discovery_markers)
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
    checks['ssh_authorized_keys_ui'] = all(marker in page for marker in (
        'id="row_ssh_keys"',
        "spoiler_toggle('authorized_keys')",
        'name="scripts.authorized_keys"',
        "showhide_div('row_ssh_keys', v)",
        'textarea_sshd_enabled(v)',
    ))
    checks['ssh_authorized_keys_init'] = bool(re.search(
        r"if\(!found_app_sshd\(\)\)\{[\s\S]*?"
        r"showhide_div\('wr_ssh_status_row', 0\);\s*\}else\{[\s\S]*?"
        r"wrSSHRender\(<% wr_ssh_process_state\(\); %>\);\s*"
        r"window\.setInterval\(wrSSHRefresh, 30000\);\s*"
        r"sshd_auth_change\(\);\s*\}", page))
    httpd = (root / 'usr/sbin/httpd').read_bytes()
    checks['runtime_status_backend'] = b'wr_ssh_process_state' in httpd
    process_status_handlers = (
        b'wr_ssh_process_state', b'wr_cron_process_state',
        b'wr_dns_process_state', b'wr_privoxy_process_state',
        b'wr_iperf3_process_state', b'wr_ss_client_process_state',
        b'wr_usbip_state',
    )
    checks['shared_process_observer_handlers'] = all(
        marker in httpd for marker in process_status_handlers)
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
                'WRADSCUnknown', 'WRADSCObservedNote', 'WRVLMCSObservedTitle',
                'WRVLMCSOff', 'WRVLMCSRunning', 'WRVLMCSMissing', 'WRVLMCSUnknown',
                'WRVLMCSStillRunning', 'WRVLMCSRefresh', 'WRVLMCSObservedNote', 'WRWDGObservedTitle',
                'WRWDGOff', 'WRWDGPresent', 'WRWDGMissing', 'WRWDGUnknown',
                'WRWDGStillPresent', 'WRWDGRefresh', 'WRWDGLastObservation',
                'WRWDGNoObservation', 'WRWDGObservedNote'))
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
