#!/usr/bin/env python3
"""Verify actual staged homepage assets; this does not prove device runtime."""
import argparse
import json
import re
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('romfs', type=Path)
a = p.parse_args()
www = a.romfs / 'www'
local = Path(__file__).resolve().parent
page = (www / 'index.asp').read_text(encoding='utf-8')
assert page.count('id="wr-connected-devices"') == 1
keys=('state-current','state-stale','state-unavailable','state-updating','state-paused','state-stopped','last-observations','source-networkmap','source-radio','source-initialization','title','description','retry','source-time-unavailable','empty','no-match','source-time')
keys+=('column-device','column-connection','column-category','column-confidence','connection-associated','connection-last','connection-seen','connection-unknown','confidence-unknown','confidence-possible','confidence-high','confidence-manufacturer','confidence-user','unnamed','classification-none','last-evidence')
keys+=('network-primary','network-guest','network-iot','network-unknown','category-all','category-unknown','category-tv','notice-truncated','notice-invalid','evidence-android-host','evidence-android-dhcp','evidence-windows-host','evidence-windows-dhcp','evidence-tv-host','evidence-conflict','evidence-manual','evidence-manufacturer')
rssi_keys=tuple(json.loads((local/'rssi-labels.json').read_text(encoding='utf-8')))
keys+=rssi_keys
history_keys=tuple(json.loads((local/'history-labels.json').read_text(encoding='utf-8')))
keys+=history_keys
for section in ('wr-roaming-history','wr-rssi-history'):
    tags=re.findall(r'<section\b[^>]*id="'+section+r'".*?</section>',page,re.S)
    assert len(tags)==1,section
    for key in keys[:7]+(rssi_keys if section=='wr-rssi-history' else history_keys):
        assert 'data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' in tags[0],(section,key)
for key in keys:
    assert 'data-wr-'+key+'="<#WRDeviceStatus_'+key+'#>"' in page,key
    for locale in ('EN','UK','RU'):
        prefix = 'WRDeviceStatus_'+key+'='
        values = [line[len(prefix):].strip() for line in
                  (www/(locale+'.dict')).read_text(encoding='utf-8').splitlines()
                  if line.startswith(prefix)]
        assert len(values) == 1 and values[0] and '<#' not in values[0], (locale,key,'missing, duplicate or unresolved label')
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
