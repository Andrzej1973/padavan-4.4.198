#!/usr/bin/env python3
"""Extend isolated credential candidate with Guest admission/filter; never production install."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);args=p.parse_args()
httpd=args.source/'trunk/user/httpd';web=httpd/'web_ex.c';source=web.read_text()
def replace(old,new,count=1):
 global source
 if source.count(old)!=count:p.error('candidate anchor changed: '+old[:80])
 source=source.replace(old,new)
replace('#include "wr-shared-wifi/password-request.h"','#include "wr-shared-wifi/password-request.h"\n#include "wr-shared-wifi/guest-adapter.h"')
replace(' struct wr_modern_password_plan password;',' struct wr_modern_password_plan password;\n int guest_active;\n struct wr_modern_guest_plan guest;\n enum wr_modern_guest_error guest_error;')
replace(' struct wr_modern_password_context *request=context;\n if(request->active &&',''' struct wr_modern_password_context *request=context;
 /* Guest never participates in main SSID/key projection, including injected
  * unrelated main/radio fields. Final persistence filter drops them too. */
 if(request->guest_active &&
    ((!strncmp(key,"rt_",3) && strncmp(key,"rt_guest_",9)) ||
     (!strncmp(key,"wl_",3) && strncmp(key,"wl_guest_",9))))return NULL;
 if(request->active &&''')
replace(' if(!modern->active)return value;',' if(modern->guest_active)return wr_modern_guest_persist_value(&modern->guest,name,value);\n if(!modern->active)return value;')
replace(' if(websGetVar(wp,"wr_modern_wifi_version",NULL)) {\n  websWrite',' if(websGetVar(wp,"wr_modern_wifi_version",NULL)||websGetVar(wp,"wr_modern_guest_version",NULL)) {\n  websWrite')
replace(' modern.wp=(void *)wp;',''' modern.wp=(void *)wp;
 if(websGetVar(wp,"wr_modern_guest_version",NULL)) {
  if(wr_modern_guest_admit_reason(&modern.guest,wr_shared_cgi_read,
                          wr_shared_nv_read,(void *)wp,&modern.guest_error)!=WR_SHARED_WIFI_OK) {
   if(modern.guest_error==WR_GUEST_ERROR_RELOAD)
    websWrite(wp,"Modern Guest snapshot needs reload.");
   else
    websWrite(wp,"Invalid Modern Guest request. No settings were saved.");
   wr_modern_guest_clear(&modern.guest);return 0;
  }
  modern.guest_active=1;
 }''')
# Every existing exit clears both owned secrets, including shared-plan failure.
old='wr_modern_password_clear(&modern.password); return 0;'
if source.count(old)<2:p.error('candidate cleanup exits changed')
source=source.replace(old,'wr_modern_guest_clear(&modern.guest); '+old)
headers={name:(Path(__file__).parent/name).read_bytes() for name in ('guest-schedule.h','guest-request.h','guest-adapter.h')}
for name in headers:
 if (httpd/'wr-shared-wifi'/name).exists():p.error('Guest header already exists: '+name)
for name,data in headers.items():(httpd/'wr-shared-wifi'/name).write_bytes(data)
web.write_text(source)
print('Prepared isolated actual Guest CGI admission/filter candidate; not production or runtime acceptance')
