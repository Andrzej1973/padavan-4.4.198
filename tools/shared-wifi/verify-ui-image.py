#!/usr/bin/env python3
"""Verify shared Wi-Fi UI in actual ROMFS; no device runtime claim."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);a=p.parse_args();r=a.romfs/'www'
assert (r/'shared-wifi.js').read_bytes()==(Path(__file__).parent/'ui.js').read_bytes()
for band,name in [('rt','Advanced_Wireless2g_Content.asp'),('wl','Advanced_Wireless_Content.asp')]:
 s=(r/name).read_text(encoding='utf-8')
 assert s.count('data-wr-shared-choice')==1
 assert s.count('src="/shared-wifi.js"')==1
 assert 'name="wr_wifi_shared" value="0" disabled' in s
 assert 'name="wr_wifi_source" value="'+band+'" disabled' in s
 assert s.index('WRSharedWifi.prepare(document.form, "'+band+'")')<s.index('showLoading();')
for lang in ('EN','UK','RU'):
 s=(r/(lang+'.dict')).read_text(encoding='utf-8')
 for key in ('Label','Off','On','Note','Keep','Error'):assert 'WR_WIFI_SHARED_'+key+'=' in s
print('PASS shared Wi-Fi actual ROMFS UI assets and request hooks; runtime unverified')
