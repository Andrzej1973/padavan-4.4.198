#!/usr/bin/env python3
"""Execute actual prepared Guest CGI preflight prefix and field filter; host only."""
import pathlib,subprocess,sys,tarfile,tempfile,re,json
here=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-modern-guest-candidate-') as scratch:
 root=pathlib.Path(scratch)
 with tarfile.open(sys.argv[1]) as archive:
  for name in ('httpd/web_ex.c','httpd/variables.c','shared/defaults.c'):
   p=root/'trunk/user'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.extractfile('trunk/user/'+name).read())
 for tool in (here.parent/'prepare-shared-wifi.py',here/'prepare-password-candidate.py',here/'prepare-guest-candidate.py'):
  subprocess.run(['python3',str(tool),str(root)],check=True)
 source=(root/'trunk/user/httpd/web_ex.c').read_text()
 helpers=source[source.index('#include "wr-shared-wifi/adapter.h"'):source.index('static void\nvalidate_cgi')]
 legacy=source[source.index('validate_cgi(webs_t'):source.index('validate_asp_apply(webs_t')]
 assert legacy.index('wr_modern_guest_version')<legacy.index('for (v = GetVariables')
 function=source[source.index('update_variables_ex('):]
 assert function.count('wr_modern_guest_clear(&modern.guest)')>=3
 prefix=function[function.index('{')+1:function.index('\twhile ((serviceId = svc_pop_list')]
 fixture=(here/'check-guest-adapter.c').read_text().split('int main(void)')[0]
 fixture=fixture.replace('#include "guest-adapter.h"','#include "guest-adapter.h"\n#include "adapter.h"')
 stubs=r'''
 typedef void *webs_t;
 static int errors,reached;
 static unsigned long long restart_needed_bits;
 static char *websGetVar(webs_t wp,char *key,char *fallback){const char *v=cgi(wp,key);return (char *)(v?v:fallback);}
 static char *nvram_safe_get(const char *key){if(!strcmp(key,"wr_wifi_shared"))return "1";return (char *)nv(NULL,key);}
 static int websWrite(webs_t wp,const char *fmt,...){(void)wp;(void)fmt;errors++;return 0;}
 '''
 tail=r'''
 (void)sid;(void)serviceId;(void)result;(void)action_mode;(void)sid_list;(void)script;
 reached++;
 assert(modern.guest_active&&!modern.active&&shared.plan.mode==WR_SHARED_INDEPENDENT);
 assert(!strcmp(modern.guest.band,band));
 const char *blocked[]={"rt_ssid","wl_ssid","rt_wpa_psk","rt_radio_x","rt_iot_enable","wr_wifi_shared","scripts.ap_script.sh"};
 for(unsigned int i=0;i<sizeof(blocked)/sizeof(blocked[0]);i++){
  const char *value=wr_shared_wifi_value(&shared,blocked[i],"injected");
  assert(!wr_modern_persist_value(&modern,&shared,blocked[i],value));
 }
 char key[40];snprintf(key,sizeof(key),"%s_guest_wpa_psk",band);
 assert(!strcmp(wr_modern_persist_value(&modern,&shared,key,NULL),"stored-guest-key"));
 wr_modern_guest_clear(&modern.guest);wr_modern_password_clear(&modern.password);return 0;
 }
 int main(void){
  run(NULL);assert(reached==1&&!errors&&reads==1);
  band="wl";sid="WLANConfig11a;";run(NULL);assert(reached==2&&!errors&&reads==2);
  version="bad";run(NULL);assert(reached==2&&errors==1&&reads==2);version="1";
  inject="wr_modern_wifi_version";run(NULL);assert(reached==2&&errors==2&&reads==2);inject=NULL;
  values[11]="24002500";run(NULL);assert(reached==2&&errors==3&&reads==2);
  puts("PASS actual generated Guest CGI preflight/filter: both bands with main shared1, namespace injection blocked, bad metadata/schedule reject before secret; not full persistence/runtime");
 }
 '''
 (root/'fixture.c').write_text(fixture+stubs+helpers+'\nstatic int run(webs_t wp){\n'+prefix+tail)
 subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),'-I'+str(root/'trunk/user/httpd/wr-shared-wifi'),str(root/'fixture.c'),'-o',str(root/'fixture')],check=True)
 subprocess.run([str(root/'fixture')],check=True)
 # Complete actual persistence and notification functions with in-memory NVRAM.
 template=(here/'persistence-fixture.c.inc').read_text().split('static void reset(')[0]
 begin=template.index('static char *websGetVar(');end=template.index('static int get_login_safe(',begin)
 template=template[:begin]+'''static char *guest_cgi(webs_t,char *,char *);
static char *websGetVar(webs_t wp,char *name,char *fallback){return guest_cgi(wp,name,fallback);}
'''+template[end:]
 fields=['enable','ssid','closed','auth_mode','wpa_mode','crypto','lan_isolate','ap_isolate','macrule','mcs_mode','date_x','time_x','time2_x','wpa_psk']
 for number,band in [(2,'rt'),(5,'wl')]:
  begin=template.index('static struct variable table'+str(number)+'[]=');end=template.index('};',begin)
  rows=''.join('{"'+band+'_guest_'+field+'","",NULL,'+str(1 if number==2 else 2)+'},' for field in fields if field!="ssid")
  body=template[begin:end].replace("{NULL,NULL,NULL,0}",rows+"{NULL,NULL,NULL,0}")
  template=template[:begin]+body+template[end:]
 actual_start=source.index('validate_asp_apply(webs_t');actual_end=source.index('\n}',actual_start)+2
 actual='static int\n'+source[actual_start:actual_end]
 callbacks=[]
 for marker,signature in [('nvram_commit_safe(void)','static void'),('asus_nvram_commit(int','static int'),('ej_notify_services(int','static int')]:
  begin=source.index(marker);end=source.index('\n}',begin)+2;callbacks.append(signature+'\n'+source[begin:end])
 lifecycle='\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored "-Wunused-parameter"\n'+'\n'.join(callbacks)+'\n#pragma GCC diagnostic pop\n'
 template=template.replace('/* GENERATED_HELPERS */',helpers).replace('/* GENERATED_APPLY */',actual+lifecycle)
 template+=(here/'guest-persistence-main.c.inc').read_text()
 (root/'fixture.c').write_text(template)
 subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(root/'fixture.c'),'-o',str(root/'fixture')],check=True)
 subprocess.run([str(root/'fixture')],check=True)

 # Repeat against all actual WLAN names/types (conditional branches unioned).
 variables=(root/'trunk/user/httpd/variables.c').read_text();counts=[]
 for number,service in [(2,'11b'),(5,'11a')]:
  tail=variables[variables.index('struct variable variables_WLANConfig'+service+'[] = {'):]
  body=tail[:re.search(r'^\s*};',tail,re.M).start()]
  rows=re.findall(r'\{\s*"([^"\n]+)"\s*,\s*"([^"\n]*)"\s*,',body);assert len(rows)>=80;counts.append(len(rows))
  begin=template.index('static struct variable table'+str(number)+'[]=');end=template.index('};',begin)+2
  entries=[f' {{{json.dumps(name)},{json.dumps(kind)},NULL,{1 if number==2 else 2}}}' for name,kind in rows]
  table='static struct variable table'+str(number)+'[]={\n'+',\n'.join(entries)+',\n {NULL,NULL,NULL,0}};'
  template=template[:begin]+table+template[end:]
 (root/'fixture.c').write_text(template)
 subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(root/'fixture.c'),'-o',str(root/'fixture')],check=True)
 subprocess.run([str(root/'fixture')],check=True)
 print('PASS actual WLAN name/type union',counts,'with malicious non-Guest fields; fixture events, not target-config acceptance')
