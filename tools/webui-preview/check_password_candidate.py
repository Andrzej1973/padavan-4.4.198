#!/usr/bin/env python3
"""Execute actual generated credential/shared preflight prefix, not HTTP persistence."""
import argparse
import re
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('archive',type=Path)
args=parser.parse_args()
here=Path(__file__).resolve().parent
stubs=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef void *webs_t;
struct fixture {int modern,shared,errors,reached,reads;const char *posted,*intent,*sid,*script;};
static struct fixture *current;
static unsigned long long restart_needed_bits;
static char *websGetVar(webs_t wp,char *name,char *fallback) {
 struct fixture *f=wp;const char *v=NULL;
 if(!strcmp(name,"wr_modern_wifi_version"))v=f->modern==2?"":f->modern==3?"invalid":f->modern?"1":NULL;
 else if(!strcmp(name,"wr_modern_wifi_band"))v="rt";
 else if(!strcmp(name,"wr_modern_expected_shared"))v=f->shared?"1":"0";
 else if(!strcmp(name,"wr_modern_password_intent"))v=f->intent;
 else if(!strcmp(name,"action_mode"))v=" Apply ";
 else if(!strcmp(name,"action_script"))v=f->script;
 else if(!strcmp(name,"sid_list"))v=f->sid;
 else if(!strcmp(name,"rt_ssid"))v="Stored";
 else if(!strcmp(name,"rt_auth_mode"))v="psk";
 else if(!strcmp(name,"rt_wep_x"))v="0";
 else if(!strcmp(name,"rt_wpa_mode"))v="2";
 else if(!strcmp(name,"rt_crypto"))v="aes";
 else if(!strcmp(name,"rt_wpa_psk"))v=f->posted;
 return (char *)(v?v:fallback);
}
static char *nvram_safe_get(const char *name) {
 if(!strcmp(name,"wr_wifi_shared"))return current->shared?"1":"0";
 assert(!strcmp(name,"rt_wpa_psk"));current->reads++;return "stored-passphrase";
}
static int websWrite(webs_t wp,const char *format,...) {
 struct fixture *f=wp;(void)format;f->errors++;return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-modern-generated-preflight-') as scratch:
    root=Path(scratch)
    with tarfile.open(args.archive) as archive:
        for name in ('httpd/web_ex.c','httpd/variables.c','shared/defaults.c'):
            path=root/'trunk/user'/name
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_bytes(archive.extractfile('trunk/user/'+name).read())
    for tool in (here.parent/'prepare-shared-wifi.py',here/'prepare-password-candidate.py'):
        subprocess.run(['python3',str(tool),str(root)],check=True)
    source=(root/'trunk/user/httpd/web_ex.c').read_text()
    legacy_start=source.index('validate_cgi(webs_t')
    legacy_end=source.index('\n}',legacy_start)+2
    legacy=source[legacy_start:legacy_end]
    assert legacy.index('Modern credential requests require coordinated apply.')<legacy.index('for (v = GetVariables')

    helpers=source[source.index('#include "wr-shared-wifi/adapter.h"'):source.index('static void\nvalidate_cgi')]
    start=source.index('update_variables_ex(')
    end=source.index('\n}',start)
    function=source[start:end]
    assert all('wr_modern_password_clear' in line for line in function.splitlines() if 'return 0;' in line)
    prefix=function[function.index('{')+1:function.index('\twhile ((serviceId = svc_pop_list')]
    assert source.index('wr_shared_wifi_value(shared, name, value);') < source.index('wr_modern_persist_value(modern, shared, name, value);')
    assert function.count('validate_asp_apply(wp, sid, &shared, &modern)')==3
    test=stubs+helpers+'\nstatic int run(webs_t wp) {\n'+prefix+r'''
 (void)sid;(void)serviceId;(void)result;(void)action_mode;(void)sid_list;(void)script;
 current->reached++;
 if(modern.active) {
  assert(wr_modern_persist_value(&modern,&shared,"rt_channel","13")==NULL);
  assert(wr_modern_persist_value(&modern,&shared,"wl_channel","149")==NULL);
  assert(wr_modern_persist_value(&modern,&shared,"rt_guest_ssid","injected")==NULL);
  assert(wr_modern_persist_value(&modern,&shared,"wl_guest_wpa_psk","injected")==NULL);
  assert(wr_modern_persist_value(&modern,&shared,"rt_ssid2","encoded-injection")==NULL);
  assert(wr_modern_persist_value(&modern,&shared,"rt_ssid_extra","prefix-injection")==NULL);
  assert(wr_modern_persist_value(&modern,&shared,"unrelated","injected")==NULL);
  assert(!strcmp(wr_modern_persist_value(&modern,&shared,"rt_ssid","Stored"),"Stored"));
 } else assert(!strcmp(wr_modern_persist_value(&modern,&shared,"wl_channel","149"),"149"));

 if(shared.plan.mode==WR_SHARED_SYNC) {
  const char *value=wr_shared_wifi_value(&shared,"wl_wpa_psk",NULL);
  assert(value && !strcmp(value,current->posted?current->posted:"stored-passphrase"));
  assert(wr_modern_persist_value(&modern,&shared,"wl_wpa_psk",value)==value);
 }
 wr_modern_password_clear(&modern.password);
 return 0;
}
int main(void) {
 struct fixture f={1,1,0,0,0,NULL,"keep","WLANConfig11b;WLANConfig11a;",""};
 current=&f;run(&f);assert(f.reached==1 && f.errors==0 && f.reads==1);
 f.modern=2;f.reached=f.errors=f.reads=0;run(&f);assert(f.reached==0 && f.errors==1 && f.reads==0);
 f.errors=0;legacy_guard_fixture(&f);assert(f.reached==0 && f.errors==1);
 f.modern=3;f.errors=0;run(&f);assert(f.reached==0 && f.errors==1 && f.reads==0);
 f.errors=0;legacy_guard_fixture(&f);assert(f.reached==0 && f.errors==1);
 f.modern=0;f.reached=f.errors=f.reads=0;run(&f);
 assert(f.reached==0 && f.errors==1 && f.reads==0);
 f.modern=1;f.script="unsafe";f.errors=0;run(&f);
 assert(f.reached==0 && f.errors==1 && f.reads==0);
 f.script="";f.intent="change";f.posted="new-passphrase";f.errors=0;run(&f);
 assert(f.reached==1 && f.errors==0 && f.reads==0);
 f.modern=0;f.shared=0;f.sid="WLANConfig11b;";f.reached=f.errors=0;run(&f);
 assert(f.reached==1 && f.errors==0);
 puts("PASS actual generated preflight: explicit keep reaches shared plan, legacy missing PSK still rejected, script blocked before secret read, change uses posted key; not service-loop/runtime proof");return 0;
}
'''
    # Execute the guard extracted from the actual legacy validator before any
    # table lookup. Ordinary no-marker Classic input still reaches its boundary.
    guard=legacy[legacy.index(' if(websGetVar'):legacy.index('\tfor (v = GetVariables')]
    test+= '\nstatic void legacy_guard_fixture(webs_t wp){\n'+guard+'\ncurrent->reached++;\n}\n'
    test=test.replace('int main(void) {','static void legacy_guard_fixture(webs_t wp);\nint main(void) {',1)
    test=test.replace(' current=&f;run(&f);', ' current=&f;legacy_guard_fixture(&f);assert(f.errors==1 && f.reached==0 && f.reads==0);f.modern=0;legacy_guard_fixture(&f);assert(f.reached==1);f.modern=1;f.errors=f.reached=0;run(&f);',1)
    cfile=root/'fixture.c'
    cfile.write_text(test)
    binary=root/'check'
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(cfile),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    apply_start=source.index('validate_asp_apply(webs_t')
    apply_end=source.index('\n}',apply_start)+2
    actual_apply='static int\n'+source[apply_start:apply_end]
    callbacks=[]
    for marker,signature in [('nvram_commit_safe(void)','static void'),('asus_nvram_commit(int','static int'),('ej_notify_services(int','static int')]:
        callback_start=source.index(marker)
        callback_end=source.index('\n}',callback_start)+2
        callbacks.append(signature+'\n'+source[callback_start:callback_end])
    lifecycle='\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored \"-Wunused-parameter\"\n'+'\n'.join(callbacks)+'\n#pragma GCC diagnostic pop\n'
    persistence=(here/'persistence-fixture.c.inc').read_text().replace('/* GENERATED_HELPERS */',helpers).replace('/* GENERATED_APPLY */',actual_apply+lifecycle)
    cfile.write_text(persistence)
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(cfile),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    # Repeat with every name/type from the generated WLAN tables. Conditional
    # branches are unioned deliberately; event flags remain fixture constants.
    variables=(root/'trunk/user/httpd/variables.c').read_text()
    full=persistence
    counts=[]
    for sid,service in enumerate(('11b','11a')):
        tail=variables[variables.index('struct variable variables_WLANConfig'+service+'[] = {'):]
        body=tail[:re.search(r'^\s*};',tail,re.M).start()]
        rows=re.findall(r'\{\s*"([^"\n]+)"\s*,\s*"([^"\n]*)"\s*,',body)
        assert len(rows)>=80
        counts.append(len(rows))
        table='static struct variable table'+str(sid==1 and 5 or 2)+'[]={'
        begin=full.index(table);end=full.index('};',begin)+2
        entries=[f' {{{json.dumps(name)},{json.dumps(kind)},NULL,{3 if name=="wr_wifi_shared" else sid+1}}}' for name,kind in rows]
        replacement=table+'\n'+',\n'.join(entries)+',\n {NULL,NULL,NULL,0}};'
        full=full[:begin]+replacement+full[end:]
    boundary=' return fallback;}'
    assert full.count(boundary)==1
    injection=r"""
 {int t;struct variable *entry;
  for(t=0;t<2;t++)for(entry=GetVariables(t);entry->name;entry++)if(!strcmp(entry->name,name)) {
   const char *suffix=(!strncmp(name,"rt_",3)||!strncmp(name,"wl_",3))?name+3:name;
   if(!strcmp(suffix,"ssid")||!strcmp(suffix,"auth_mode")||!strcmp(suffix,"wep_x")||!strcmp(suffix,"wpa_mode")||!strcmp(suffix,"crypto")||!strcmp(suffix,"wpa_psk")||!strcmp(name,"wr_wifi_shared"))return fallback;
   return "injected";
  }
 }
"""
    full=full.replace(boundary,injection+boundary)
    cfile.write_text(full)
    subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined',
                    '-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(cfile),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
    print('PASS all generated WLAN field names/types:',counts,'conditional union; fixture event constants, not target-config proof')

print('Candidate source/compiler scratch removed')
