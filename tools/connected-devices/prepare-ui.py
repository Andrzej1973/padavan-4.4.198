#!/usr/bin/env python3
"""Keep passive Wi-Fi observation panels off the router homepage."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
page = a.source / 'trunk/user/www/n56u_ribbon_fixed/index.asp'
content = page.read_text(encoding='utf-8')
if content.count('                <!--Body content-->') != 1 or content.count('</head>') != 1:
    raise SystemExit('Homepage anchors changed; no files written')
for marker in ('wr-observation-launcher', 'wr-connected-devices',
               'wr-roaming-history', 'wr-rssi-history', 'wr_view=',
               '/wr-device-'):
    if marker in content:
        raise SystemExit('Observer UI is present on the homepage: ' + marker)
print('Homepage has no observation panels or launch links; background collectors remain enabled')
