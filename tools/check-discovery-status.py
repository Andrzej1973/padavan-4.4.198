#!/usr/bin/env python3
"""Exercise discovery, KMS and watchdog observers and emitted page without services."""
import argparse
import ast
from pathlib import Path
import re
import shutil
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
here = Path(__file__).resolve().parent
root = args.output.resolve()
process_observers = (
    'prepare-dns-process-status.py', 'prepare-ssh-status.py',
    'prepare-cron-status.py', 'prepare-privoxy-status.py',
    'prepare-iperf3-status.py', 'prepare-shadowsocks-status.py',
    'prepare-usbip-status.py',
)
for name in process_observers:
    source = (here / name).read_text(encoding='utf-8')
    assert 'pids(' not in source, name + ' must not use binary pids() semantics'
    assert 'wr_process_present(' in source, name + ' must use the error-aware proc scanner'
user = root / 'trunk/user'
(user / 'httpd').mkdir(parents=True, exist_ok=True)
www = user / 'www/n56u_ribbon_fixed'
www.mkdir(parents=True, exist_ok=True)
(user / 'httpd/web_ex.c').write_text(
    '#include <stdio.h>\n'
    'struct ej_handler ej_handlers[] =\n{\n'
    '\t{ "json_system_status", ej_system_status_hook},\n};\n')
page = www / 'Advanced_Services_Content.asp'
page.write_text('''function initial(){
\tchange_crond_enabled();
}
function applyRule(){ }
<tr id="lltd"><th><#Adm_Svc_lltd#></th><td></td></tr>
<tr id="adsc"><th><#Adm_Svc_adsc#></th><td></td></tr>
<tr id="div_vlmcsd"><th>KMS activation</th><td></td></tr>
<tr id="watchdog"><th><#TweaksWdg#></th><td></td></tr>
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
image_verifier = (here / 'verify-discovery-status-image.py').read_text(encoding='utf-8')
for marker in ('required_page', 'backend_markers',
               'id="wrVlmcsd_status_row"', 'id="wrWatchdog_status_row"',
               'WRVLMCSObservedNote', 'WRWDGObservedNote',
               'watchdog_cpu', '/sys/module/rt_timer_wdg', 'MT7621',
               "('EN.dict', 'UK.dict', 'RU.dict')"):
    assert marker in image_verifier, ('image verifier must cover KMS/watchdog status', marker)
assert html.count('wr_lltd_process_state();') == 1
assert html.count('wr_adsc_process_state();') == 1
assert html.count('wr_vlmcsd_process_state();') == 1
assert html.count('wr_watchdog_module_state();') == 1
assert html.count("window.setInterval(function(){wrLLTDRefresh();wrADSCRefresh();wrVlmcsdRefresh();wrWatchdogRefresh();},30000)") == 1
assert "vlmcsd:'wr_vlmcsd_process_state'" in html
assert 'id="wrVlmcsd_process_status"' in html
assert 'function wrVlmcsdRefresh()' in html
assert 'data:{output:outputs[service]}' in html
assert 'generation === wrDiscoveryGeneration[service]' in html
assert 'Date.now() - wrDiscoverySampledAt[service] >= 45000' in html
for locale in ('EN.footer', 'UK.dict', 'RU.dict'):
    translated = (dictionary / locale).read_text(encoding='utf-8')
    for key in ('WRLLDTPresent=', 'WRLLDTUnknown=', 'WRLLTDObservedNote=',
                'WRADSCPresent=', 'WRADSCUnknown=', 'WRADSCObservedNote=',
                'WRVLMCSOff=', 'WRVLMCSRunning=', 'WRVLMCSMissing=',
                'WRVLMCSUnknown=', 'WRVLMCSStillRunning=', 'WRVLMCSRefresh=',
                'WRVLMCSLastObservation=', 'WRVLMCSNoObservation=',
                'WRVLMCSObservedNote=',
                'WRWDGOff=', 'WRWDGPresent=', 'WRWDGMissing=', 'WRWDGUnknown=',
                'WRWDGStillPresent=', 'WRWDGRefresh=', 'WRWDGLastObservation=',
                'WRWDGNoObservation=', 'WRWDGObservedNote='):
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
wrVlmcsdRefresh();assert.equal(request.data.output,'wr_vlmcsd_process_state');
wrWatchdogRefresh();assert.equal(request.data.output,'wr_watchdog_module_state');
wrDiscoveryRender('vlmcsd',1);assert.equal(elements.wrVlmcsd_process_status.className,'text-success');
wrDiscoveryRender('vlmcsd',null);assert.equal(elements.wrVlmcsd_process_status.textContent,wrDiscoveryLabels.vlmcsd[3]);
assert.equal(elements.wrVlmcsd_observed_at.textContent,'<#WRVLMCSNoObservation#>');
console.log('PASS emitted LLTD/ASUS/KMS bounded observation, refresh and expiry');
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
#define _POSIX_C_SOURCE 200809L
#include <assert.h>
#include <dirent.h>
#include <errno.h>
#include <fcntl.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#ifdef _WIN32
#include <direct.h>
#define mkdir(path,mode) _mkdir(path)
#define rmdir(path) _rmdir(path)
#define setenv(name,value,overwrite) _putenv_s(name,value)
#endif
#define R_OK 4
#define X_OK 1
#ifndef S_IFDIR
#define S_IFDIR 0040000
#endif
#ifndef S_IFREG
#define S_IFREG 0100000
#endif
typedef FILE *webs_t;
static int proc_unavailable, proc_readdir_error, comm_unreadable, lld_binary_missing, adsc_binary_missing, vlmcsd_binary_missing;
static int sysfs_unavailable, sysfs_not_dir, watchdog_module_present, watchdog_stat_error;
static int lltd_requested, adsc_requested, vlmcsd_requested, watchdog_requested;
static char output[16];
static int mock_access(const char *path, int mode) {
 if (!strcmp(path,"/proc") && mode==(R_OK|X_OK)) return proc_unavailable;
 if (mode==X_OK && !proc_unavailable && ((!strcmp(path,"/bin/lld2d") && !lld_binary_missing) ||
     (!strcmp(path,"/usr/sbin/infosvr") && !adsc_binary_missing) ||
     (!strcmp(path,"/usr/bin/vlmcsd") && !vlmcsd_binary_missing))) return 0;
 if (!strcmp(path,"/bin/lld2d") && mode==X_OK) return lld_binary_missing;
 if (!strcmp(path,"/usr/sbin/infosvr") && mode==X_OK) return adsc_binary_missing;
 if (!strcmp(path,"/usr/bin/vlmcsd") && mode==X_OK) return vlmcsd_binary_missing;
 if (!strcmp(path,"/sys/module") && mode==(R_OK|X_OK)) return sysfs_unavailable;
 assert(0); return -1;
}
static DIR *mock_opendir(const char *path) {
 const char *dir=getenv("WR_DISCOVERY_TEST_PROC");
 if (!strcmp(path,dir)) return proc_unavailable ? (errno=EACCES,(DIR*)NULL) : opendir(dir);
 return opendir(path);
}
static struct dirent *mock_readdir(DIR *dir) { if(proc_readdir_error){errno=EIO;return NULL;}struct dirent *entry=readdir(dir);if(!entry)errno=0;return entry; }
static int mock_closedir(DIR *dir) { return closedir(dir); }
static FILE *mock_fopen(const char *path,const char *mode) {
 const char *dir=getenv("WR_DISCOVERY_TEST_PROC"); char expected[512];
 snprintf(expected,sizeof(expected),"%s/321/comm",dir);
 if (!strcmp(path,expected) && comm_unreadable) { errno=EACCES; return NULL; }
 return fopen(path,mode);
}
static char *mock_fgets(char *buffer,int size,FILE *file) { return fgets(buffer,size,file); }
static int mock_ferror(FILE *file) { return ferror(file); }
static int mock_stat(const char *path, struct stat *buffer) {
 if (!strcmp(path,"/sys/module")) {
  if (sysfs_unavailable) { errno=ENOENT; return -1; }
  buffer->st_mode=sysfs_not_dir ? S_IFREG : S_IFDIR; return 0;
 }
 if (!strcmp(path,"/sys/module/rt_timer_wdg")) {
  if (watchdog_module_present) { buffer->st_mode=S_IFDIR; return 0; }
  errno=watchdog_stat_error ? watchdog_stat_error : ENOENT; return -1;
 }
 assert(0); errno=ENOENT; return -1;
}
static int nvram_get_int(const char *key) {
 if (!strcmp(key,"lltd_enable")) return lltd_requested;
 if (!strcmp(key,"adsc_enable")) return adsc_requested;
 if (!strcmp(key,"vlmcsd_enable")) return vlmcsd_requested;
 if (!strcmp(key,"watchdog_cpu")) return watchdog_requested;
 assert(0); return 0;
}
static int websWrite(webs_t wp, const char *format, ...) {
 va_list args; int n; (void)wp; va_start(args,format);
 n=vsnprintf(output,sizeof(output),format,args); va_end(args); return n;
}
'''+backend.replace('access(', 'mock_access(').replace('stat(', 'mock_stat(').replace('opendir(', 'mock_opendir(').replace('readdir(', 'mock_readdir(').replace('closedir(', 'mock_closedir(').replace('fopen(', 'mock_fopen(').replace('fgets(', 'mock_fgets(').replace('ferror(', 'mock_ferror(')+r'''
static void expect(int (*handler)(int,webs_t,int,char**),int expected) {
 handler(0,NULL,0,NULL); if(output[0]!='0'+expected){fprintf(stderr,"expected %d, got %s\\n",expected,output);assert(output[0]=='0'+expected);}
}
int main(void) {
 char procdir[]="discovery-proc-XXXXXX";
 assert(mkdtemp(procdir));
 setenv("WR_DISCOVERY_TEST_PROC",procdir,1);
 { char path[512]; FILE *f; snprintf(path,sizeof(path),"%s/321",procdir);assert(!mkdir(path,0700));strcat(path,"/comm");f=fopen(path,"w");assert(f);fputs("idle\n",f);fclose(f); }
 assert(wr_process_present("idle")==1);
 assert(wr_process_present("not-running")==0);
 proc_unavailable=1;assert(wr_process_present("idle")==-1);proc_unavailable=0;
 proc_readdir_error=1;assert(wr_process_present("idle")==-1);proc_readdir_error=0;
 comm_unreadable=1;assert(wr_process_present("idle")==-1);comm_unreadable=0;
 lltd_requested=0;expect(ej_wr_lltd_process_state,0);
 lltd_requested=1;expect(ej_wr_lltd_process_state,2);
 { char path[512]; FILE *f;snprintf(path,sizeof(path),"%s/321/comm",procdir);f=fopen(path,"w");assert(f);fputs("lld2d\n",f);fclose(f); }
 expect(ej_wr_lltd_process_state,1);
 lltd_requested=0;expect(ej_wr_lltd_process_state,4);
 proc_unavailable=1;expect(ej_wr_lltd_process_state,3);proc_unavailable=0;
 proc_readdir_error=1;expect(ej_wr_lltd_process_state,3);proc_readdir_error=0;
 comm_unreadable=1;expect(ej_wr_lltd_process_state,3);comm_unreadable=0;
 { char path[512];snprintf(path,sizeof(path),"%s/321/comm",procdir);assert(!unlink(path)); }
 proc_unavailable=0;lld_binary_missing=1;expect(ej_wr_lltd_process_state,3);
 lld_binary_missing=0;adsc_requested=1;expect(ej_wr_adsc_process_state,2);
 adsc_binary_missing=1;expect(ej_wr_adsc_process_state,3);
 ej_wr_adsc_process_state(0,NULL,1,NULL);assert(!strcmp(output,"3"));
 vlmcsd_requested=0;expect(ej_wr_vlmcsd_process_state,0);
 vlmcsd_requested=1;expect(ej_wr_vlmcsd_process_state,2);
 vlmcsd_binary_missing=1;expect(ej_wr_vlmcsd_process_state,3);
 vlmcsd_binary_missing=0;ej_wr_vlmcsd_process_state(0,NULL,1,NULL);assert(!strcmp(output,"3"));
 watchdog_requested=0;watchdog_module_present=0;expect(ej_wr_watchdog_module_state,0);
 watchdog_requested=1;watchdog_module_present=1;expect(ej_wr_watchdog_module_state,1);
 watchdog_module_present=0;expect(ej_wr_watchdog_module_state,2);
 watchdog_requested=0;watchdog_module_present=1;expect(ej_wr_watchdog_module_state,4);
 watchdog_requested=1;watchdog_module_present=0;sysfs_unavailable=1;expect(ej_wr_watchdog_module_state,3);
 sysfs_unavailable=0;sysfs_not_dir=1;expect(ej_wr_watchdog_module_state,3);
 sysfs_not_dir=0;watchdog_stat_error=EACCES;expect(ej_wr_watchdog_module_state,3);
 ej_wr_watchdog_module_state(0,NULL,1,NULL);assert(!strcmp(output,"3"));
 { char dir[512];snprintf(dir,sizeof(dir),"%s/321",procdir);assert(!rmdir(dir));assert(!rmdir(procdir)); }
 puts("PASS shared proc scanner reports present/absent and fails closed on proc, enumeration and comm errors; LLTD/ASUS/KMS and watchdog fixtures pass");
 return 0;
}
'''
c_file = root / 'discovery.c'
c_file.write_text(c_test, encoding='utf-8')
exe = root / 'discovery-check'
subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                '-DWR_DISCOVERY_STATUS_TEST', str(c_file), '-o', str(exe)], check=True)
try:
    subprocess.run([str(exe)], check=True, cwd=str(root))
finally:
    # mkdtemp() in the generated C fixture is relative to its working dir.
    # Remove only its exact six-character random directory names, even when
    # an assertion or an interrupt stops the fixture before its own cleanup.
    for procdir in root.glob('discovery-proc-*'):
        if re.fullmatch(r'discovery-proc-[A-Za-z0-9]{6}', procdir.name) and \
                procdir.is_dir() and not procdir.is_symlink():
            shutil.rmtree(procdir)
