#!/usr/bin/env python3
"""Verify the homepage omits observer UI while the background APIs remain linked."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('romfs', type=Path)
a = p.parse_args()
www = a.romfs / 'www'
page = (www / 'index.asp').read_text(encoding='utf-8')
for marker in ('wr-observation-launcher', 'wr-connected-devices',
               'wr-roaming-history', 'wr-rssi-history', 'wr_view=',
               '/wr-device-'):
    assert marker not in page, 'Observer UI leaked onto homepage: ' + marker

# Keep the runtime interfaces and action history in the image. The separate
# build checks verify that httpd calls wr_device_background_tick() on its own
# loop, independent of whether a page requests these endpoints.
daemon = (a.romfs / 'usr/sbin/httpd').read_bytes()
for marker in (b'wr_devices.json', b'wr_roaming.json', b'wr_rssi.json',
               b'/var/run/wr-device-observer/actions',
               b'/var/run/wr-band-steering.lock', b'/usr/sbin/wr-band-steering',
               b'monitoringGap', b'interruptions', b'ioctl_accepted',
               b'ioctl_failed', b'driver_ack', b'remove_candidate'):
    assert marker in daemon, 'Missing linked background observer marker: ' + marker.decode('ascii')
print('PASS homepage contains no observer windows; background collection APIs and action history remain in image')
