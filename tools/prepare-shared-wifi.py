#!/usr/bin/env python3
"""Install shared Wi-Fi preflight before all HTTP apply-loop persistence."""
import argparse
from pathlib import Path
parser=argparse.ArgumentParser()
parser.add_argument('source',type=Path)
a=parser.parse_args()
root=a.source/'trunk/user'
changes=[]
f=root/'httpd/web_ex.c';s=f.read_text(encoding='utf-8')
if 'wr_shared_wifi_prepare' in s: raise ValueError('Shared Wi-Fi already prepared')
anchor='static int\nvalidate_asp_apply(webs_t wp, int sid)'
if s.count(anchor)!=1 or s.count('validate_asp_apply(wp, sid)')!=3: raise ValueError('Apply entry anchors changed')
helpers=r'''#include "wr-shared-wifi/adapter.h"
static const char *wr_shared_cgi_read(void *ctx, const char *key)
{
 return websGetVar((webs_t)ctx, (char *)key, NULL);
}
static const char *wr_shared_nv_read(void *ctx, const char *key)
{
 (void)ctx;
 return nvram_safe_get(key);
}

'''
s=s.replace(anchor,helpers+'static int\nvalidate_asp_apply(webs_t wp, int sid, const struct wr_shared_wifi_adapter *shared)')
s=s.replace('validate_asp_apply(wp, sid)','validate_asp_apply(wp, sid, &shared)')
lookup='\t\tvalue = websGetVar(wp, name, NULL);'
start=s.index('validate_asp_apply(webs_t');end=s.index('update_variables_ex(',start)
part=s[start:end]
if part.count(lookup)!=1: raise ValueError('Apply variable lookup changed')
part=part.replace(lookup,lookup+'\n\t\tvalue = (char *)wr_shared_wifi_value(shared, name, value);')
s=s[:start]+part+s[end:]
start=s.index('update_variables_ex(')
part=s[start:]
part=part.replace('\tint sid;','\tint sid;\n\tstruct wr_shared_wifi_adapter shared;',1)
anchor='\tsid_list = websGetVar(wp, "sid_list", "");\n'
if part.count(anchor)<1: raise ValueError('Service list anchor missing')
preflight=r'''
 /* Entire request is checked before any service table or script can write. */
 if (wr_shared_wifi_prepare(&shared, (void *)wp, wr_shared_cgi_read,
                            wr_shared_nv_read) != WR_SHARED_WIFI_OK ||
     (shared.plan.mode != WR_SHARED_INDEPENDENT &&
      (strcmp(action_mode, " Apply ") && strcmp(action_mode, " Restart ") &&
       strcmp(action_mode, "  Save  "))) ||
     (shared.plan.mode != WR_SHARED_INDEPENDENT && *script)) {
  websWrite(wp, "<script>alert('Invalid shared Wi-Fi request. No settings were saved.');</script>\n");
  return 0;
 }
'''
part=part.replace(anchor,anchor+preflight,1);s=s[:start]+part
# Legacy CGI must not bypass coordinated apply or overwrite its results.
old='validate_cgi(webs_t wp, int sid)'
if s.count(old)!=1 or s.count('validate_cgi(wp, sid)')!=4: raise ValueError('Legacy CGI anchors changed')
s=s.replace(old,'validate_cgi(webs_t wp, int sid, const struct wr_shared_wifi_adapter *shared)')
s=s.replace('validate_cgi(wp, sid)','validate_cgi(wp, sid, &shared)',1)
s=s.replace('validate_cgi(wp, sid)','validate_cgi(wp, sid, NULL)')
old='if ((value = websGetVar(wp, name, NULL))) {'
if s.count(old)!=1: raise ValueError('Legacy CGI value lookup changed')
s=s.replace(old,'value = websGetVar(wp, name, NULL);\n\t\tif (shared) value = (char *)wr_shared_wifi_value(shared, name, value);\n\t\tif (value) {')
# Helpers/header must precede validate_cgi as its signature uses the adapter type.
s=s.replace(helpers,'',1)
s=s.replace('static void\nvalidate_cgi',helpers+'static void\nvalidate_cgi',1)
legacy='\t\tchar *sid_list, *serviceId;\n\t\tint sid;'
if s.count(legacy)!=1: raise ValueError('Legacy route declaration changed')
s=s.replace(legacy,legacy+'\n\t\tstruct wr_shared_wifi_adapter legacy_shared;')
anchor='\t\tsid_list = websGetVar(wp, "sid_list", "");\n'
if s.count(anchor)!=1: raise ValueError('Legacy route service anchor changed')
s=s.replace(anchor,anchor+'''\t\tif (wr_shared_wifi_prepare(&legacy_shared, (void *)wp, wr_shared_cgi_read,
                            wr_shared_nv_read) != WR_SHARED_WIFI_OK ||
            legacy_shared.plan.mode != WR_SHARED_INDEPENDENT) {
            websWrite(wp, "Shared Wi-Fi changes require coordinated apply.");
            return 0;
        }
''')
changes.append((f,s))
f=root/'httpd/variables.c';s=f.read_text(encoding='utf-8')
anchor='struct variable variables_WLANConfig11b[] = {'
if s.count(anchor)!=1: raise ValueError('Wi-Fi service table changed')
s=s.replace(anchor,anchor+'\n\t\t\t{"wr_wifi_shared", "", NULL, EVM_RESTART_WIFI2|EVM_RESTART_WIFI5},')
changes.append((f,s))
f=root/'shared/defaults.c';s=f.read_text(encoding='utf-8')
anchor='#if BOARD_HAS_5G_RADIO'
if anchor not in s: raise ValueError('Default anchor missing')
s=s.replace(anchor,'\t{ "wr_wifi_shared", "0" },\n'+anchor,1)
changes.append((f,s))
for name in ('validate.h','plan.h','adapter.h'):
 target=root/'httpd/wr-shared-wifi'/name
 if target.exists(): raise ValueError('Shared header already exists')
 changes.append((target,(Path(__file__).parent/'shared-wifi'/name).read_text(encoding='utf-8')))
for f,s in changes:
 f.parent.mkdir(parents=True,exist_ok=True);f.write_text(s,encoding='utf-8')
print('Installed shared Wi-Fi preflight, coherent lookups and default-off selector')
