#!/usr/bin/env python3
"""Check actual Wi-Fi QR ROMFS assets; does not prove phone connectivity."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('romfs',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
checks={};files={}
def read(name):
 f=a.romfs/'www'/name;b=f.read_bytes() if f.is_file() else b''
 checks[name+'_present']=bool(b);files[name]={'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()};return b
assets=['wifi-qrcode-renderer.js','wifi-qr-payload.js','wifi-qr-preview.js']
for name in assets:
 checks[name+'_exact']=read(name)==(Path(__file__).parent/name).read_bytes()
for band,name in [('rt','Advanced_Wireless2g_Content.asp'),('wl','Advanced_Wireless_Content.asp')]:
 b=read(name)
 checks[name+'_show']=('onclick="wrWifiQrShow(\''+band+'\')"').encode() in b
 checks[name+'_hide']=b'wrWifiQrHide()' in b
 checks[name+'_message']=b'id="wr_wifi_qr_message"' in b
 positions=[b.find(('/'+asset).encode()) for asset in assets]
 checks[name+'_dependencies']=all(x>=0 for x in positions) and positions==sorted(positions)
for lang in ['EN','UK','RU']:
 b=read(lang+'.dict')
 for key in ['Show','Hide','Error','Preview']:checks[lang+'_'+key]=('WR_WIFI_QR_'+key+'=').encode() in b
report={'checks':checks,'files':files,'runtime_verified':False,'scope':'ROMFS asset inclusion and exact contents; no phone connection proof'}
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
if not all(checks.values()):raise SystemExit('Wi-Fi QR image checks failed: '+', '.join(k for k,v in checks.items() if not v))
print('Wi-Fi QR image assets verified; device runtime unverified')
