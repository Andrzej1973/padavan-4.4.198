#!/usr/bin/env python3
"""Test structural image gate with synthetic files; this is not firmware QA."""
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-eoip-image-') as directory:
    root = Path(directory)
    def write(name, data):
        path = root/name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path
    for name, source in [('www/Advanced_Services_EoIP.asp','status-page.asp'),
                         ('www/bootstrap/js/wr-eoip-status.js','status-view.js'),
                         ('www/bootstrap/js/wr-eoip-editor.js','settings-editor.js'),
                         ('usr/bin/wr-eoip-boot','boot.sh')]:
        write(name, (here/source).read_bytes()).chmod(0o755)
    write('www/Advanced_Services_Content.asp', b'Advanced_Services_EoIP.asp')
    keys = set(re.findall(r'<#(WREOIP\w+)#>', (here/'status-page.asp').read_text()))
    dictionary = ''.join(key+'=fixture\n' for key in sorted(keys)).encode()
    for language in ('EN','UK','RU'): write('www/'+language+'.dict', dictionary)
    http = b'wr_eoip_status wr_eoip_token wr_eoip_settings wr_eoip_settings.cgi saved_in_ram apply_requested apply_eoip settings_rolled_back invalid_token_or_confirmation operation-lock'
    write('usr/sbin/httpd', http)
    write('usr/bin/eoip-service', b'boot-stored apply-stored stop-table validate-table /sbin/modprobe').chmod(0o755)
    defaults = ['eoip_enable'] + [f'eoip_slot{slot}_{key}' for slot in range(8)
        for key in ('enable','autostart','local','remote','id','mtu','keepalive','retries','bridge')]
    write('lib/libshared.so', ' '.join(defaults).encode())
    report = root/'report.json'
    command = [sys.executable, str(here/'verify-image.py'), str(root), '--report', str(report)]
    subprocess.run(command, check=True, capture_output=True)
    assert json.loads(report.read_text())['runtime_verified'] is False
    write('usr/sbin/httpd', http.replace(b'wr_eoip_token', b'missing'))
    assert subprocess.run(command, capture_output=True).returncode != 0
    write('usr/sbin/httpd', http)
    write('www/UK.dict', dictionary + (sorted(keys)[0]+'=duplicate\n').encode())
    assert subprocess.run(command, capture_output=True).returncode != 0
print('PASS EoIP image gate fixture: complete inputs accepted, missing HTTP marker and duplicate label rejected')
