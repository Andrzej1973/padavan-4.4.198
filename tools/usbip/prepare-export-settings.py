#!/usr/bin/env python3
"""Install authenticated USB/IP export settings and default-off restore control."""
import argparse
from pathlib import Path

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--config',type=Path,required=True)
a=p.parse_args()
if 'CONFIG_FIRMWARE_INCLUDE_USBIP=y' not in a.config.read_text().splitlines():
    raise SystemExit(0)
root=a.source/'trunk/user/httpd';here=Path(__file__).parent
path=root/'web_ex.c';text=path.read_text(encoding='utf-8')
anchor='struct mime_handler mime_handlers[] = {'
route='\t{ "wr_usbip_action.cgi*",'
entry='\t{ "wr_usbip_job_state", ej_wr_usbip_job_state},\n'
if any(text.count(x)!=1 for x in (anchor,route,entry)) or 'wr_usbip_settings_output' in text:
    raise SystemExit('USBIP export settings anchors changed')
text=text.replace(anchor,(here/'http-settings.inc').read_text(encoding='utf-8')+'\n'+anchor,1)
text=text.replace(route,'\t{ "wr_usbip_settings.cgi*", "application/json", no_cache_IE, wr_usbip_settings_input, wr_usbip_settings_output, 1 },\n'+route,1)
text=text.replace(entry,entry+'\t{ "wr_usbip_export_settings", ej_wr_usbip_export_settings},\n',1)
include=root/'wr-usbip';include.mkdir(exist_ok=True)
for name in ['export-rules.h','export-codec.h','export-store.h','export-settings.h']:
    (include/name).write_text((here/name).read_text(encoding='utf-8'),encoding='utf-8',newline='\n')
path.write_text(text,encoding='utf-8',newline='\n')
print('Prepared safe-session USBIP settings POST/read endpoint; no automatic device actions')
