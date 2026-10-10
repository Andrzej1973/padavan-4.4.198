#!/usr/bin/env python3
"""Verify actual staged homepage assets; this does not prove device runtime."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('romfs', type=Path)
a = p.parse_args()
www = a.romfs / 'www'
local = Path(__file__).resolve().parent
page = (www / 'index.asp').read_text(encoding='utf-8')
assert page.count('id="wr-connected-devices"') == 1
assert 'id="statusframe"' in page
assert page.index('id="wr-connected-devices"') < page.index('id="statusframe"')
total = 0
for name in ('classify', 'refresh', 'homepage', 'roaming', 'roaming-view', 'rssi', 'rssi-view', 'boot'):
    target = 'wr-device-' + name + '.js'
    content = (www / target).read_bytes()
    assert content == (local / (name + '.js')).read_bytes(), target
    assert page.count('src="/' + target + '"') == 1, target
    total += len(content)
css = (www / 'wr-device-homepage.css').read_bytes()
assert css == (local / 'homepage.css').read_bytes()
assert page.count('href="/wr-device-homepage.css"') == 1
daemon = (a.romfs / 'usr/sbin/httpd').read_bytes()
assert b'wr_devices.json' in daemon
assert b'wr_roaming.json' in daemon
assert b'wr_rssi.json' in daemon
assert page.count('id="wr-rssi-history"') == 1
# Actual HTTP binary must contain the background endpoint, verified producer
# paths and separate command-evidence serializer, not just the old route.
for marker in (b'/var/run/wr-device-observer/actions', b'/var/run/wr-band-steering.lock',
               b'/usr/sbin/wr-band-steering', b'monitoringGap', b'interruptions',
               b'ioctl_accepted', b'ioctl_failed', b'driver_ack', b'remove_candidate'):
    assert marker in daemon, 'Missing linked action observer marker: ' + marker.decode('ascii')
assert b'Band Steering commands' in (www / 'wr-device-roaming-view.js').read_bytes()

assert page.count('id="wr-roaming-history"') == 1
print('PASS staged homepage, exact assets and linked observation/action JSON markers; raw asset bytes:', total + len(css))
