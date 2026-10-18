#!/usr/bin/env python3
"""Exercise LLTD/ASUS process observers and the emitted page without services."""
import argparse
import ast
from pathlib import Path
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
here = Path(__file__).resolve().parent
root = args.output.resolve()
user = root / 'trunk/user'
(user / 'httpd').mkdir(parents=True, exist_ok=True)
www = user / 'www/n56u_ribbon_fixed'
www.mkdir(parents=True, exist_ok=True)
(user / 'httpd/web_ex.c').write_text(
    'struct ej_handler ej_handlers[] =\n{\n'
    '\t{ "json_system_status", ej_system_status_hook},\n};\n')
page = www / 'Advanced_Services_Content.asp'
page.write_text('''function initial(){
\tchange_crond_enabled();
}
function applyRule(){ }
<tr id="lltd"><th><#Adm_Svc_lltd#></th><td></td></tr>
<tr id="adsc"><th><#Adm_Svc_adsc#></th><td></td></tr>
<tr id="row_crontabs" style="display:none">
\twrCronRender(<% wr_cron_process_state(); %>);
\twindow.setInterval(wrCronRefresh,30000);''')
dictionary = user / 'www/dict'
dictionary.mkdir(parents=True, exist_ok=True)
for name in ('EN.footer', 'UK.dict', 'RU.dict'):
    (dictionary / name).write_text('')
subprocess.run([sys.executable, str(here / 'prepare-discovery-status.py'),
                str(root)], check=True)
html = page.read_text(encoding='utf-8')
assert html.count('wr_lltd_process_state();') == 1
assert html.count('wr_adsc_process_state();') == 1
assert html.count("window.setInterval(function(){wrLLTDRefresh();wrADSCRefresh();},30000)") == 1
assert 'generation === wrDiscoveryGeneration[service]' in html
assert 'Date.now() - wrDiscoverySampledAt[service] >= 45000' in html
for locale in ('EN.footer', 'UK.dict', 'RU.dict'):
    translated = (dictionary / locale).read_text(encoding='utf-8')
    for key in ('WRLLDTPresent=', 'WRLLDTUnknown=', 'WRLLTDObservedNote=',
                'WRADSCPresent=', 'WRADSCUnknown=', 'WRADSCObservedNote='):
        assert key in translated, (locale, key)

script = re.search(r'var wrDiscoveryBusy[\s\S]*?(?=function applyRule)', html).group(0)
node_test = r'''
const assert=require('node:assert/strict');
const elements={},timers=[],listeners={};let request,success,always;
const document={hidden:false,getElementById:id=>elements[id]||=( {} ),addEventListener:(name,cb)=>listeners[name]=cb};
const window={setTimeout:(cb,delay)=>{assert.equal(delay,45000);timers.push(cb);}};
const $j={ajax:options=>{request=options;return {done(cb){success=cb;return this;},fail(){return this;},always(cb){always=cb;return this;}};}};
'''+script+r'''
wrDiscoveryRender('lltd',1);const old=timers[0];
wrDiscoveryRender('lltd',2);old();assert.equal(elements.wrLLTD_process_status.textContent,wrDiscoveryLabels.lltd[2]);
timers[1]();assert.equal(elements.wrLLTD_process_status.textContent,wrDiscoveryLabels.lltd[3]);
document.hidden=true;wrLLTDRefresh();assert.equal(request,undefined);
document.hidden=false;wrLLTDRefresh();assert.equal(request.data.output,'wr_lltd_process_state');
assert.equal(request.timeout,5000);assert.equal(request.cache,false);
success(1);always();assert.equal(elements.wrLLTD_process_status.textContent,wrDiscoveryLabels.lltd[1]);
wrADSCRefresh();assert.equal(request.data.output,'wr_adsc_process_state');
console.log('PASS emitted LLTD/ASUS bounded observation, refresh and expiry');
'''
node_file = root / 'discovery.js'
node_file.write_text(node_test, encoding='utf-8')
subprocess.run(['node', str(node_file)], check=True)

tree = ast.parse((here / 'prepare-discovery-status.py').read_text(encoding='utf-8'))
backend = next(ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign) and
               any(isinstance(target, ast.Name) and target.id == 'backend_code'
                   for target in node.targets))
c_test = r'''
#include <assert.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#define R_OK 4
#define X_OK 1
typedef FILE *webs_t;
static int proc_unavailable, lld_binary_missing, adsc_binary_missing;
static int lltd_requested, lltd_active, adsc_requested, adsc_active;
static char output[16];
static int access(const char *path, int mode) {
 if (!strcmp(path,"/proc/self/stat") && mode==R_OK) return proc_unavailable;
 if (!strcmp(path,"/bin/lld2d") && mode==X_OK) return lld_binary_missing;
 if (!strcmp(path,"/usr/sbin/infosvr") && mode==X_OK) return adsc_binary_missing;
 assert(0); return -1;
}
static int nvram_get_int(const char *key) {
 if (!strcmp(key,"lltd_enable")) return lltd_requested;
 if (!strcmp(key,"adsc_enable")) return adsc_requested;
 assert(0); return 0;
}
static int pids(const char *name) {
 if (!strcmp(name,"lld2d")) return lltd_active;
 if (!strcmp(name,"infosvr")) return adsc_active;
 assert(0); return -1;
}
static int websWrite(webs_t wp, const char *format, ...) {
 va_list args; int n; (void)wp; va_start(args,format);
 n=vsnprintf(output,sizeof(output),format,args); va_end(args); return n;
}
'''+backend+r'''
static void expect(int (*handler)(int,webs_t,int,char**),int expected) {
 handler(0,NULL,0,NULL); assert(output[0]=='0'+expected);
}
int main(void) {
 lltd_requested=0;lltd_active=0;expect(ej_wr_lltd_process_state,0);
 lltd_requested=1;lltd_active=1;expect(ej_wr_lltd_process_state,1);
 lltd_active=0;expect(ej_wr_lltd_process_state,2);
 lltd_requested=0;lltd_active=1;expect(ej_wr_lltd_process_state,4);
 lltd_active=-1;expect(ej_wr_lltd_process_state,3);
 lltd_active=1;proc_unavailable=1;expect(ej_wr_lltd_process_state,3);
 proc_unavailable=0;lld_binary_missing=1;expect(ej_wr_lltd_process_state,3);
 lld_binary_missing=0;adsc_requested=1;adsc_active=1;expect(ej_wr_adsc_process_state,1);
 adsc_active=0;expect(ej_wr_adsc_process_state,2);
 adsc_active=-1;expect(ej_wr_adsc_process_state,3);
 adsc_active=1;adsc_binary_missing=1;expect(ej_wr_adsc_process_state,3);
 ej_wr_adsc_process_state(0,NULL,1,NULL);assert(!strcmp(output,"3"));
 puts("PASS LLTD/ASUS configured versus process states and unknown conditions");
 return 0;
}
'''
c_file = root / 'discovery.c'
c_file.write_text(c_test, encoding='utf-8')
exe = root / 'discovery-check'
subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                str(c_file), '-o', str(exe)], check=True)
subprocess.run([str(exe)], check=True)
