#!/usr/bin/env python3
"""Synthetic checks for homepage removal and retained background endpoints."""
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

local = Path(__file__).resolve().parent
root = Path.cwd() / ('image-gate-' + uuid.uuid4().hex)
assert root.resolve().parent == Path.cwd()
www = root / 'www'
www.mkdir(parents=True)
(root / 'usr/sbin').mkdir(parents=True)
page = '<html><body><iframe id="statusframe"></iframe></body></html>'
markers = (b'wr_devices.json', b'wr_roaming.json', b'wr_rssi.json',
           b'/var/run/wr-device-observer/actions', b'/var/run/wr-band-steering.lock',
           b'/usr/sbin/wr-band-steering', b'monitoringGap', b'interruptions',
           b'ioctl_accepted', b'ioctl_failed', b'driver_ack', b'remove_candidate')
(www / 'index.asp').write_text(page, encoding='utf-8')
daemon = root / 'usr/sbin/httpd'
daemon.write_bytes(b'\0'.join(markers))

def check(ok):
    result = subprocess.run([sys.executable, str(local / 'verify-ui-image.py'), str(root)],
                            capture_output=True)
    assert (result.returncode == 0) == ok, result.stderr.decode()

try:
    check(True)
    for marker in ('wr-observation-launcher', 'wr-connected-devices',
                   'wr-roaming-history', 'wr-rssi-history', 'wr_view=',
                   '/wr-device-'):
        (www / 'index.asp').write_text(page.replace('</body>', marker + '</body>'), encoding='utf-8')
        check(False)
    (www / 'index.asp').write_text(page, encoding='utf-8')
    check(True)
    for missing in markers:
        daemon.write_bytes(b'\0'.join(marker for marker in markers if marker != missing))
        check(False)
finally:
    assert root.resolve().parent == Path.cwd()
    shutil.rmtree(root)
print('PASS image gate rejects homepage observer UI and missing background endpoints')
