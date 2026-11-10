#!/usr/bin/env python3
"""Prepare isolated Modern credential CGI candidate on a shared-Wi-Fi source tree.

Not called by firmware CI/production installer. Radio-field admission and complete
form/response integration remain separate requirements before enabling Apply.
"""
import argparse
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('source',type=Path)
args=parser.parse_args()
httpd=args.source/'trunk/user/httpd'
web=httpd/'web_ex.c'
source=web.read_text()
if 'wr_modern_password_context' in source:
    parser.error('credential candidate already installed')
anchor='static void\nvalidate_cgi'
if source.count(anchor)!=1 or '#include "wr-shared-wifi/adapter.h"' not in source:
    parser.error('shared Wi-Fi preparation required')
helpers='''#include "wr-shared-wifi/password-request.h"
struct wr_modern_password_context {
 void *wp;
 int active;
 const char *band;
 struct wr_modern_password_plan password;
};
static const char *wr_modern_cgi_read(void *context,const char *key)
{
 struct wr_modern_password_context *request=context;
 if(request->active &&
    ((!strcmp(request->band,"rt") && !strcmp(key,"rt_wpa_psk")) ||
     (!strcmp(request->band,"wl") && !strcmp(key,"wl_wpa_psk"))))
  return request->password.value;
 return wr_shared_cgi_read(request->wp,key);
}
static const char *wr_modern_nv_read(void *context,const char *key)
{
 struct wr_modern_password_context *request=context;
 return wr_shared_nv_read(request->wp,key);
}
'''
filter_code = r"""
/* This candidate admits credentials only. Radio/guest/other table fields cannot
 * reach persistence until a separate complete validator is bound. */
static const char *wr_modern_persist_value(
 const struct wr_modern_password_context *modern,
 const struct wr_shared_wifi_adapter *shared,const char *name,const char *value)
{
 static const char *const fields[]={"ssid","auth_mode","wep_x","wpa_mode","crypto","wpa_psk"};
 const char *prefix;unsigned int i;
 if(!modern->active)return value;
 if(!strcmp(name,"wr_wifi_shared"))return value;
 prefix=!strcmp(modern->band,"rt")?"rt_":"wl_";
 if(!strncmp(name,prefix,3) ||
    (shared->plan.mode==WR_SHARED_SYNC &&
     (!strncmp(name,"rt_",3)||!strncmp(name,"wl_",3)))) {
  for(i=0;i<sizeof(fields)/sizeof(fields[0]);i++)
   if(!strcmp(name+3,fields[i]))return value;
 }
 return NULL;
}
"""
helpers+=filter_code
source=source.replace(anchor,helpers+anchor,1)
signature='validate_asp_apply(webs_t wp, int sid, const struct wr_shared_wifi_adapter *shared)'
if source.count(signature)!=1:
    parser.error('actual apply validator signature changed')
source=source.replace(signature,signature[:-1]+', const struct wr_modern_password_context *modern)',1)
lookup='value = (char *)wr_shared_wifi_value(shared, name, value);'
apply_start=source.index('validate_asp_apply(webs_t')
apply_end=source.index('update_variables_ex(',apply_start)
apply_body=source[apply_start:apply_end]
if apply_body.count(lookup)!=1:
    parser.error('actual shared persistence value anchor changed')
apply_body=apply_body.replace(lookup,lookup+'\n\t\tvalue = (char *)wr_modern_persist_value(modern, shared, name, value);',1)
source=source[:apply_start]+apply_body+source[apply_end:]
start=source.index('update_variables_ex(')
end=source.index('\n}',start)+2
function=source[start:end]
declaration='\tstruct wr_shared_wifi_adapter shared;'
if function.count(declaration)!=1:
    parser.error('shared request declaration changed')
function=function.replace(declaration,declaration+'\n\tstruct wr_modern_password_context modern = {0};',1)
preflight=' /* Entire request is checked before any service table or script can write. */'
if function.count(preflight)!=1:
    parser.error('shared preflight anchor changed')
modern=''' modern.wp=(void *)wp;
 if(websGetVar(wp,"wr_modern_wifi_version",NULL)) {
  if(wr_modern_password_request(&modern.password,wr_shared_cgi_read,
                               wr_shared_nv_read,(void *)wp)!=WR_SHARED_WIFI_OK) {
   websWrite(wp,"Invalid Modern credential request. No settings were saved.");
   return 0;
  }
  modern.band=websGetVar(wp,"wr_modern_wifi_band",NULL);
  modern.active=1;
 }
'''
function=function.replace(preflight,modern+preflight,1)
old='wr_shared_wifi_prepare(&shared, (void *)wp, wr_shared_cgi_read,\n                            wr_shared_nv_read)'
if function.count(old)!=1:
    parser.error('shared preflight call changed')
function=function.replace(old,'wr_shared_wifi_prepare(&shared, &modern, wr_modern_cgi_read,\n                            wr_modern_nv_read)',1)
call='validate_asp_apply(wp, sid, &shared)'
if function.count(call)!=3:
    parser.error('actual service-loop validator calls changed')
function=function.replace(call,'validate_asp_apply(wp, sid, &shared, &modern)')
# Service dispatch remains existing code; its actual validation lookup now applies
# the Modern credential filter after shared-plan value projection.
function=function.replace('return 0;', 'wr_modern_password_clear(&modern.password); return 0;')
source=source[:start]+function+source[end:]
headers={name:(Path(__file__).parent/name).read_bytes() for name in ('password-intent.h','password-request.h')}
for name in headers:
    if (httpd/'wr-shared-wifi'/name).exists():
        parser.error('candidate header already exists: '+name)
# All anchors/header availability checked before the first mutation.
for name,data in headers.items():
    (httpd/'wr-shared-wifi'/name).write_bytes(data)
web.write_text(source)
print('Prepared isolated actual CGI credential preflight candidate; not production integration or Apply acceptance')
