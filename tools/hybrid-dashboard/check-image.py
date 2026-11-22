#!/usr/bin/env python3
"""Verify installed hybrid assets and required Classic routes in ROMFS."""
import argparse
import hashlib
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
args = parser.parse_args()
here = Path(__file__).resolve().parent
www = args.source / 'trunk/romfs/www'
assets = ('index.html', 'dashboard.css', 'dashboard.js',
          'iot-status.html', 'iot-status.css', 'iot-status.js')
classic = ('index.asp', 'system_status_data.asp', 'status_wanlink.asp',
           'status_lanlink.asp', 'device-map/internet.asp', 'device-map/intranet.asp',
           'device-map/clients.asp', 'Main_WStatus2g_Content.asp',
           'Advanced_Wireless_Content.asp', 'Main_LogStatus_Content.asp')
config = (args.source / 'trunk/.config').read_text().splitlines()
sqm = 'CONFIG_FIRMWARE_INCLUDE_SQM=y' in config
sqm_page = www / 'Advanced_SQM.asp'
if sqm:
    classic += ('Advanced_SQM.asp',)
elif sqm_page.exists() or sqm_page.is_symlink():
    raise SystemExit('Unexpected Classic SQM page with SQM disabled')
for name in assets:
    actual = www / 'hybrid' / name
    expected = (here / name).read_bytes()
    if name == 'index.html' and not sqm:
        link = '<a href="/Advanced_SQM.asp">Керування трафіком</a>\n'.encode()
        if expected.count(link) != 1:
            raise SystemExit('Dashboard SQM navigation anchor changed')
        expected = expected.replace(link, b'', 1)
    if not actual.is_file() or actual.read_bytes() != expected:
        raise SystemExit('Missing or altered hybrid asset: ' + name)
for name in classic:
    if not (www / name).is_file():
        raise SystemExit('Missing Classic route: ' + name)
total = sum((www / 'hybrid' / name).stat().st_size for name in assets)
if total > 100_000:
    raise SystemExit('Hybrid assets exceed 100 KB')
print('PASS hybrid ROMFS assets and Classic routes, bytes', total,
      'index SHA256', hashlib.sha256((www / 'hybrid/index.html').read_bytes()).hexdigest())
