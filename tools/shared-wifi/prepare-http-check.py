#!/usr/bin/env python3
"""Execute the actual preflight block with CGI/NVRAM stubs, not the whole server."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
s=(a.source/'trunk/user/httpd/web_ex.c').read_text(encoding='utf-8')
start=s.index('static const char *wr_shared_cgi_read(');end=s.index('static void\nvalidate_cgi',start);helpers=s[start:end]
start=s.index(' /* Entire request is checked before any service table or script can write. */');end=s.index('\n\twhile ((serviceId = svc_pop_list',start);block=s[start:end]
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(r'''#include "adapter.h"
#include <assert.h>
#include <stdio.h>
typedef void *webs_t;
struct item {const char *key;char *value;};
struct fixture {struct item *items;};
static int errors, reached_loop;
static char *websGetVar(webs_t wp,char *key,char *fallback) {
 struct fixture *f=wp;int i;
 for(i=0;f->items[i].key;i++)if(!strcmp(key,f->items[i].key))return f->items[i].value;
 return fallback;
}
static char *nvram_safe_get(const char *key) {
 return !strcmp(key,"wr_wifi_shared")?"0":!strncmp(key,"rt_",3)?"old-2g":"old-5g";
}
static int websWrite(webs_t wp,const char *format,...) {
 (void)wp;assert(strstr(format,"No settings were saved"));errors++;return 0;
}
''' + helpers + r'''
static int run_preflight(webs_t wp,const char *action_mode,const char *script) {
 struct wr_shared_wifi_adapter shared;
''' + block + r'''
 /* Instrument the boundary immediately following actual preflight. */
 reached_loop++;
 if(shared.plan.mode==WR_SHARED_SYNC){
  assert(!strcmp(wr_shared_wifi_value(&shared,"rt_ssid",NULL),"Home"));
  assert(!strcmp(wr_shared_wifi_value(&shared,"wl_ssid",NULL),"Home"));
 }else if(shared.plan.mode==WR_SHARED_DISABLE_KEEP){
  assert(!strcmp(wr_shared_wifi_value(&shared,"rt_ssid","forged"),"old-2g"));
  assert(!strcmp(wr_shared_wifi_value(&shared,"wl_ssid","forged"),"old-5g"));
 }
 return 1;
}
static void check(struct fixture *f,const char *mode,const char *script,int accepted) {
 int old_errors=errors,old_reached=reached_loop;
 assert(run_preflight(f,mode,script)==accepted);
 assert(reached_loop-old_reached==accepted);
 assert(errors-old_errors==!accepted);
}
int main(void) {
 struct item cgi[]={{"wr_wifi_shared","1"},{"wr_wifi_source","rt"},{"sid_list","WLANConfig11b;WLANConfig11a;"},{"rt_ssid","Home"},{"rt_auth_mode","psk"},{"rt_wep_x","0"},{"rt_wpa_mode","2"},{"rt_crypto","aes"},{"rt_wpa_psk","password"},{NULL,NULL}};
 struct fixture f={cgi};
 check(&f," Apply ","",1);
 check(&f," Restart ","",1);
 check(&f,"  Save  ","",1);
 check(&f,"Update","",0);
 check(&f," Add ","",0);
 check(&f," Apply ","unsafe_script",0);
 cgi[8].value="short";check(&f," Apply ","",0);
 cgi[8].value=NULL;check(&f," Apply ","",0);
 cgi[8].value="password";cgi[2].value="WLANConfig11b;";check(&f," Apply ","",0);
 cgi[0].value="0";check(&f," Apply ","",0);
 cgi[2].value="WLANConfig11b;WLANConfig11a;";check(&f," Apply ","",1);
 puts("PASS actual HTTP preflight block: rejected requests stop before loop boundary; valid sync and disable snapshots; Update and script bypass rejected");
 return 0;
}
''',encoding='utf-8')
print('Extracted actual HTTP shared preflight block for host/target checks')
