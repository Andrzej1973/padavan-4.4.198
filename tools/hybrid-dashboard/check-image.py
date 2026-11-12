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
           'Advanced_Wireless_Content.asp', 'Advanced_SQM.asp', 'Main_LogStatus_Content.asp')
for name in assets:
    actual = www / 'hybrid' / name
    if not actual.is_file() or actual.read_bytes() != (here / name).read_bytes():
        raise SystemExit('Missing or altered hybrid asset: ' + name)
for name in classic:
    if not (www / name).is_file():
        raise SystemExit('Missing Classic route: ' + name)
total = sum((www / 'hybrid' / name).stat().st_size for name in assets)
if total > 100_000:
    raise SystemExit('Hybrid assets exceed 100 KB')
print('PASS hybrid ROMFS assets and Classic routes, bytes', total,
      'index SHA256', hashlib.sha256((www / 'hybrid/index.html').read_bytes()).hexdigest())
