#!/usr/bin/env python3
"""Verify status integration files in actual ROMFS; not device behavior."""
import argparse
import hashlib
import json
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('romfs',type=Path)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
checks={}
files={}
def read(relative):
 path=a.romfs/relative
 try: blob=path.read_bytes()
 except OSError: blob=b''
 checks[relative+'_present']=bool(blob)
 files[relative]={'bytes':len(blob),'sha256':hashlib.sha256(blob).hexdigest()}
 return blob
page=read('www/Advanced_WAdvanced2g_Content.asp')
for value in (b'name="wr_bs_enable"',b'id="wr_bs_refresh"',b'id="wr_bs_status"',b'/wr-band-status.js'):
 checks['page_'+value.decode()]=value in page
asset=read('www/wr-band-status.js')
expected=(Path(__file__).parent/'status-ui.js').read_bytes()
checks['status_asset_exact']=asset==expected
httpd=read('usr/sbin/httpd')
for value in (b'wr_band_observation',b'observe_wr_band_steering',b'wr_bs_enable'):
 checks['httpd_'+value.decode()]=value in httpd
rc=read('sbin/rc')
for value in (b'observe_wr_band_steering',b'wr_bs_observation_serial'):
 checks['rc_'+value.decode()]=value in rc
for lang in ('EN','UK','RU'):
 dictionary=read('www/'+lang+'.dict')
 for key in ('Refresh','Wait','Unknown','Active','Off'):
  checks[lang+'_'+key]=('WR_BS_Status_'+key+'=').encode() in dictionary
report={'checks':checks,'files':files,'runtime_verified':False,
 'scope':'actual ROMFS assets and compiled string presence; no activation or client behavior proof'}
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if not all(checks.values()):
 raise SystemExit('Status image checks failed: '+', '.join(k for k,v in checks.items() if not v))
print('Status image assets and compiled handler strings verified; runtime unverified')
