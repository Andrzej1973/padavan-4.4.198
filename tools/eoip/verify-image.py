#!/usr/bin/env python3
"""Check EoIP files and linked hooks in ROMFS; never claim device behavior."""
import argparse
import json
import os
from pathlib import Path
import re

p = argparse.ArgumentParser()
p.add_argument('romfs', type=Path)
p.add_argument('--report', type=Path, required=True)
a = p.parse_args()
here = Path(__file__).resolve().parent
root = a.romfs.resolve()
checks = []

def require(condition, description):
    if not condition:
        raise SystemExit('FAIL EoIP image: ' + description)
    checks.append(description)

def file(name):
    path = root / name
    require(path.resolve().is_relative_to(root) and path.is_file(), 'file present within ROMFS: ' + name)
    return path

for installed, source in [
    ('www/Advanced_Services_EoIP.asp', 'status-page.asp'),
    ('www/bootstrap/js/wr-eoip-status.js', 'status-view.js'),
    ('www/bootstrap/js/wr-eoip-editor.js', 'settings-editor.js'),
    ('usr/bin/wr-eoip-boot', 'boot.sh'),
]:
    require(file(installed).read_text() == (here/source).read_text(), 'exact shipped source: ' + source)
require(os.access(root/'usr/bin/wr-eoip-boot', os.X_OK), 'executable lifecycle script')
require('Advanced_Services_EoIP.asp' in file('www/Advanced_Services_Content.asp').read_text(), 'services navigation link')
page = (here/'status-page.asp').read_text()
keys = set(re.findall(r'<#(WREOIP\w+)#>', page))
for language in ('EN', 'UK', 'RU'):
    text = file('www/' + language + '.dict').read_text()
    for key in sorted(keys):
        require(len(re.findall(r'^' + re.escape(key) + '=', text, re.M)) == 1,
                'exactly one label: ' + language + '/' + key)
http = file('usr/sbin/httpd').read_bytes()
for marker in (b'wr_eoip_status', b'wr_eoip_token', b'wr_eoip_settings', b'wr_eoip_settings.cgi',
               b'saved_in_ram', b'apply_requested', b'apply_eoip', b'settings_rolled_back',
               b'invalid_token_or_confirmation', b'operation-lock'):
    require(marker in http, 'linked HTTP marker: ' + marker.decode())
worker = file('usr/bin/eoip-service')
require(os.access(worker, os.X_OK), 'executable target worker')
binary = worker.read_bytes()
for marker in (b'boot-stored', b'apply-stored', b'stop-table', b'validate-table', b'/sbin/modprobe'):
    require(marker in binary, 'linked worker marker: ' + marker.decode())
defaults = file('lib/libshared.so').read_bytes()
require(b'eoip_enable' in defaults, 'linked master default')
for slot in range(8):
    for field in ('enable','autostart','local','remote','id','mtu','keepalive','retries','bridge'):
        key = f'eoip_slot{slot}_{field}'
        require(key.encode() in defaults, 'linked default key: ' + key)
a.report.write_text(json.dumps({'schema':1, 'checks':checks, 'image_verified':True, 'runtime_verified':False,
    'limits':'File identity, translation coverage and linked markers only; no HTTP session, reboot or tunnel transfer executed.'},
    ensure_ascii=False, indent=2) + '\n')
print('PASS EoIP ROMFS identities, labels, navigation, linked HTTP/controller/defaults; runtime unverified')
