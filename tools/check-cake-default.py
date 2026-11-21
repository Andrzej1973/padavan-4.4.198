#!/usr/bin/env python3
"""Execute actual prepared RC start helper; mocked OS, not device acceptance."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__);p.add_argument('tree',type=Path);a=p.parse_args()
s=(a.tree/'trunk/user/rc/services.c').read_text();anchor='static void start_sqm_locked(void)'
assert s.count(anchor)==1
start=s.index(anchor);helper=s[start:s.index('\n}',start)+2]
code=r'''
#include <assert.h>
#include <string.h>
static int enabled,ap,running,wan,loaded,fail,sets,reloads,calls,stops;
static int nvram_get_int(const char *key){return !strcmp(key,"sqm_enable")?enabled:running;}
static int get_ap_mode(void){return ap;}
static void get_wan_ifname(char *name){strcpy(name,wan?"eth3":"");}
static int is_interface_exist(const char *name){return !strcmp(name,"eth3");}
static void nvram_set_temp(const char *key,const char *value){assert(!strcmp(key,"sqm_running_t")&&!strcmp(value,"1"));running=1;sets++;}
static void reload_nat_modules(void){assert(running);reloads++;}
static int is_module_loaded(const char *name){(void)name;return loaded;}
static int eval(const char *path,...){assert(running&&!strcmp(path,"/usr/lib/sqm/run.sh"));calls++;return fail;}
static int stop_sqm_locked(void){stops++;running=0;return 0;}
#define logmessage(...) ((void)0)
'''+helper+r'''
int main(void){
 for(int scenario=0;scenario<7;scenario++){
  enabled=scenario!=0;ap=scenario==2;running=scenario==3;wan=scenario!=4;
  loaded=scenario==5;fail=scenario==6;sets=reloads=calls=stops=0;
  start_sqm_locked();
  if(scenario==0||scenario==2||scenario==3||scenario==4){assert(!sets&&!reloads&&!calls&&!stops);}
  else if(scenario==1){assert(running&&sets==1&&reloads==1&&calls==1&&!stops);}
  else {assert(!running&&sets==1&&reloads==1&&stops==1&&calls==(scenario==6));}
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cake-default-') as tmp:
 source=Path(tmp)/'check.c';source.write_text(code)
 binary=Path(tmp)/'check'
 subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(source),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
print('PASS actual prepared CAKE start: factory OFF has no start/inhibit calls; explicit enable, AP/running/WAN guards and failures; OS injected')
