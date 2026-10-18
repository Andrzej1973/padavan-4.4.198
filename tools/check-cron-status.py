#!/usr/bin/env python3
"""Exercise emitted Cron handler and UI without starting any service."""
import argparse
import ast
from pathlib import Path
import re
import subprocess
import sys
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
here=Path(__file__).resolve().parent;root=a.output.resolve();user=root/'trunk/user'
(user/'httpd').mkdir(parents=True,exist_ok=True);www=user/'www/n56u_ribbon_fixed';www.mkdir(parents=True,exist_ok=True)
(user/'httpd/web_ex.c').write_text('struct ej_handler ej_handlers[] =\n{\n\t{ "json_system_status", ej_system_status_hook},\n};\n')
page=www/'Advanced_Services_Content.asp'
page.write_text('function initial(){\n\tchange_crond_enabled();\n}\nfunction applyRule(){ }\n<tr id="row_crontabs" style="display:none">')
dictionary=user/'www/dict';dictionary.mkdir(parents=True,exist_ok=True)
for name in ('EN.footer','UK.dict','RU.dict'):(dictionary/name).write_text('')
subprocess.run([sys.executable,str(here/'prepare-cron-status.py'),str(root)],check=True)
html=page.read_text(encoding='utf-8');script=re.search(r'var wrCronStatusBusy[\s\S]*?(?=function applyRule)',html)[0]
assert html.count('wr_cron_process_state();')==1 and 'window.setInterval(wrCronRefresh,30000)' in html
test=r'''
const assert=require('node:assert/strict');
const elements={},timers=[],listeners={};let request;
const document={hidden:false,getElementById:id=>elements[id]||=( {} ),addEventListener:(name,cb)=>listeners[name]=cb};
const window={setTimeout:(cb,delay)=>{assert.equal(delay,45000);timers.push(cb);}};
const $j={ajax:options=>{request=options;return {done(cb){this.success=cb;return this;},fail(cb){return this;},always(cb){return this;}};}};
'''+script+r'''
wrCronRender(1);assert.equal(elements.wr_cron_process_status.textContent,'<#WRCronPresent#>');
const old=timers[0];wrCronRender(0);old();assert.equal(elements.wr_cron_process_status.textContent,'<#WRCronOff#>');
timers[1]();assert.equal(elements.wr_cron_process_status.textContent,'<#WRCronUnknown#>');
document.hidden=true;wrCronRefresh();assert.equal(request,undefined);
document.hidden=false;wrCronRefresh();assert.equal(request.data.output,'wr_cron_process_state');
assert.equal(request.timeout,5000);assert.equal(request.cache,false);
console.log('PASS emitted Cron UI observation expiry and explicit bounded refresh');
'''
js=root/'cron.js';js.write_text(test,encoding='utf-8');subprocess.run(['node',str(js)],check=True)
tree=ast.parse((here/'prepare-cron-status.py').read_text(encoding='utf-8'))
handler=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='handler' for t in n.targets))
prefix=r'''
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#define R_OK 4
#define X_OK 1
typedef FILE *webs_t;
static int requested,active,unreadable,missing;static char output[32];
static int access(const char *path,int mode){if(mode==R_OK){assert(!strcmp(path,"/proc/self/stat"));return unreadable;}assert(mode==X_OK&&!strcmp(path,"/usr/sbin/crond"));return missing;}
static int nvram_get_int(const char *key){assert(!strcmp(key,"crond_enable"));return requested;}
static int pids(const char *name){assert(!strcmp(name,"crond"));return active;}
static int websWrite(webs_t wp,const char *format,...){va_list args;int n;(void)wp;va_start(args,format);n=vsnprintf(output,sizeof(output),format,args);va_end(args);return n;}
'''
suffix=r'''
int main(void){int enabled,present;for(enabled=0;enabled<2;enabled++)for(present=0;present<2;present++){
 requested=enabled;active=present;ej_wr_cron_process_state(0,NULL,0,NULL);
 assert(output[0]=='0'+(present?(enabled?1:4):(enabled?2:0)));
}active=-1;ej_wr_cron_process_state(0,NULL,0,NULL);assert(!strcmp(output,"3"));
active=1;unreadable=1;ej_wr_cron_process_state(0,NULL,0,NULL);assert(!strcmp(output,"3"));
unreadable=0;missing=1;ej_wr_cron_process_state(0,NULL,0,NULL);assert(!strcmp(output,"3"));
missing=0;ej_wr_cron_process_state(0,NULL,1,NULL);assert(!strcmp(output,"3"));
puts("PASS emitted Cron backend configured/observed states, missing provider and observation errors");return 0;}
'''
c=root/'cron.c';c.write_text(prefix+handler+suffix);exe=root/'cron-check'
subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
subprocess.run([str(exe)],check=True)
