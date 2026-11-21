#!/usr/bin/env python3
"""Verify that disabled EoIP is not exposed or linked into final ROMFS."""
import argparse
import json
from pathlib import Path

SELECTOR = 'CONFIG_FIRMWARE_INCLUDE_EOIP'
OPTIONAL_FILES = (
    'www/Advanced_Services_EoIP.asp',
    'www/bootstrap/js/wr-eoip-status.js',
    'www/bootstrap/js/wr-eoip-editor.js',
    'usr/bin/wr-eoip-boot',
    'usr/bin/eoip-service',
)
HTTP_MARKERS = (
    b'wr_eoip_status', b'wr_eoip_token', b'wr_eoip_settings.cgi',
)


def selector_enabled(path):
    return any(line.strip() == SELECTOR + '=y'
               for line in path.read_text(encoding='utf-8').splitlines())


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('romfs', type=Path)
parser.add_argument('requested_config', type=Path)
parser.add_argument('effective_config', type=Path)
parser.add_argument('--report', type=Path, required=True)
args = parser.parse_args()
root = args.romfs.resolve()
checks = []

if selector_enabled(args.requested_config):
    raise SystemExit('FAIL EoIP exclusion: requested profile enables the EoIP selector')
if selector_enabled(args.effective_config):
    raise SystemExit('FAIL EoIP exclusion: effective image config enables the EoIP selector')
checks.extend((
    'requested selector is disabled',
    'effective image selector is disabled',
))

for relative in OPTIONAL_FILES:
    path = root / relative
    if path.exists() or path.is_symlink():
        raise SystemExit('FAIL EoIP exclusion: optional ROMFS file remains: ' + relative)
    checks.append('optional ROMFS file absent: ' + relative)

navigation = root / 'www/Advanced_Services_Content.asp'
if not navigation.is_file():
    raise SystemExit('FAIL EoIP exclusion: Administration / Services page is missing')
if b'Advanced_Services_EoIP.asp' in navigation.read_bytes():
    raise SystemExit('FAIL EoIP exclusion: optional EoIP navigation link remains')
checks.append('EoIP navigation link absent')

httpd = root / 'usr/sbin/httpd'
if not httpd.is_file():
    raise SystemExit('FAIL EoIP exclusion: final httpd is missing')
http_bytes = httpd.read_bytes()
for marker in HTTP_MARKERS:
    if marker in http_bytes:
        raise SystemExit('FAIL EoIP exclusion: linked HTTP handler remains: ' + marker.decode())
    checks.append('HTTP marker absent: ' + marker.decode())

report = {
    'schema': 1,
    'feature': 'eoip',
    'feature_selected': False,
    'image_verified': True,
    'runtime_verified': False,
    'checks': checks,
    'limits': 'Confirms disabled selector and absent EoIP ROMFS page, navigation, worker and HTTP markers; no device behavior tested.',
}
args.report.parent.mkdir(parents=True, exist_ok=True)
args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print('PASS disabled EoIP selector and final ROMFS absence; runtime unverified')
