#!/usr/bin/env python3
"""Static ROMFS evidence for USBIP settings; no runtime/device acceptance."""
import argparse
import hashlib
import json
from pathlib import Path
import re
p=argparse.ArgumentParser(description=__doc__);p.add_argument('tree',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=a.tree/'trunk/romfs';page=root/'www/Advanced_Printer_others.asp';httpd=root/'usr/sbin/httpd'
text=page.read_text(encoding='utf-8');binary=httpd.read_bytes();checks={}
checks['exact_settings_js']=Path(__file__).with_name('settings-view.js').read_text(encoding='utf-8').strip() in text
for marker in ['wrUSBIPSettingsLoad();','id="wr_usbip_settings_rows"','id="wr_usbip_settings_ack"',
               'id="wr_usbip_settings_save"','id="wr_usbip_settings_add"']:
    checks['page:'+marker]=marker in text
for marker in ['wr_usbip_settings.cgi','wr_usbip_export_settings','/etc/storage/usbip',
               '/var/run/wr-usbip.lock','wr-usbip-exports-v1','"applied":false','"flash_committed":false']:
    checks['linked:'+marker]=marker.encode() in binary
keys=set(re.findall(r'<#(WRUSBIPSettings\w+)#>',text));checks['settings_key_count']=len(keys)==16
hashes={}
for name in ['EN.dict','UK.dict','RU.dict']:
    path=root/'www'/name;lines=path.read_text(encoding='utf-8').splitlines()
    for key in sorted(keys):
        values=[line.split('=',1)[1] for line in lines if line.startswith(key+'=')]
        checks[name+':'+key]=len(values)==1 and bool(values[0].strip())
    hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
for path in [page,httpd]:hashes[path.name]=hashlib.sha256(path.read_bytes()).hexdigest()
report={'schema':1,'runtime_verified':False,'scope':'USBIP settings ROMFS/static linkage; restore not implemented',
        'success':all(checks.values()),'checks':checks,'sha256':hashes}
a.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(('PASS' if report['success'] else 'FAIL')+' USBIP settings image checks')
raise SystemExit(0 if report['success'] else 1)
