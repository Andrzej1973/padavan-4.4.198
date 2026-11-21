#!/usr/bin/env python3
"""Execute actual prepared Guest CGI preflight prefix and field filter; host only."""
import pathlib,subprocess,sys,tarfile,tempfile,re,json
here=pathlib.Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-modern-guest-candidate-') as scratch:
 root=pathlib.Path(scratch)
 with tarfile.open(sys.argv[1]) as archive:
  for name in ('httpd/web_ex.c','httpd/httpd.c','httpd/cgi.c','httpd/variables.c','shared/defaults.c'):
   p=root/'trunk/user'/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(archive.extractfile('trunk/user/'+name).read())
 for tool in (here.parent/'prepare-shared-wifi.py',here/'prepare-password-candidate.py',here/'prepare-guest-candidate.py',here/'prepare-guest-transport.py',here/'prepare-modern-body.py',here/'prepare-guest-json.py'):
  subprocess.run(['python3',str(tool),str(root)],check=True)
 source=(root/'trunk/user/httpd/web_ex.c').read_text()
 server=(root/'trunk/user/httpd/httpd.c').read_text()
 request=server[server.index('handle_request(FILE *conn_fp, const conn_item_t *item)'):]
 assert request.index('wr_modern_guest_post_authorized = 0;')<request.index('fgets(line,')
 assert request.index('if (!auth_check(authorization))')<request.index('wr_modern_guest_post_authorized = wr_modern_guest_transport_allowed(')<request.index('handler->input(file,')
 assert 'strncasecmp(cur, "X-WR-Modern:", 12)' in request

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
 static int errors,reached,transport_allowed=1;
 int wr_modern_guest_post_allowed(void){return transport_allowed;}
 void wr_modern_guest_input_fail(void){}
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
  values[11]="08002200";transport_allowed=0;run(NULL);assert(reached==2&&errors==4&&reads==2);
  version=NULL;inject="wr_modern_wifi_version";run(NULL);assert(reached==2&&errors==5&&reads==2);
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
 update_start=source.index('update_variables_ex(');update_end=source.index('\n}',update_start)+2
 update='static int\n'+source[update_start:update_end]
 whole_stubs=r"""
 int wr_modern_guest_post_allowed(void){return 1;}
 void wr_modern_guest_input_fail(void){}
 typedef unsigned int u32;
 #define GROUP_FLAG_ADD 1
 #define GROUP_FLAG_REMOVE 2
 #define EVM_RESTART_WAN (1ULL<<10)
 #define EVM_RESTART_IPV6 (1ULL<<11)
 #define EVT_RESTART_WAN 30
 #define EVT_RESTART_WIFI2 8
 #define EVT_RESTART_WIFI5 8
 #define EVT_RESTART_REBOOT 60
 #define MAX(a,b) ((a)>(b)?(a):(b))
 static char *svc_pop_list(char *list,char separator){static char name[64];char *end=strchr(list,separator);size_t n;if(!*list)return NULL;assert(end);n=(size_t)(end-list);assert(n<sizeof(name));memcpy(name,list,n);name[n]=0;return name;}
 static const char *GetServiceId(int sid){return sid==0?"WLANConfig11b":sid==1?"WLANConfig11a":NULL;}
 static int response_done,response_unchanged,response_errors,response_conflicts;
 static int websWrite(webs_t wp,const char *fmt,...){(void)wp;if(strstr(fmt,"done_committing"))response_done++;else if(strstr(fmt,"no_changes_and_no_committing"))response_unchanged++;else if(strstr(fmt,"Invalid Modern"))response_errors++;else if(strstr(fmt,"Modern Guest snapshot needs reload")){response_errors++;response_conflicts++;}return 0;}
 static int apply_cgi_group(webs_t wp,int sid,void *unused,const char *id,int flag){(void)wp;(void)sid;(void)unused;(void)id;(void)flag;abort();return 0;}
 static void nvram_clr_group_temp(struct variable *v){(void)v;abort();}
 static void validate_cgi(webs_t wp,int sid,const struct wr_shared_wifi_adapter *shared){(void)wp;(void)sid;(void)shared;abort();}
 static int eval(const char *name){(void)name;abort();return 0;}
 static void sys_script(const char *name){(void)name;abort();}
 static int nvram_match(const char *name,const char *value){return !strcmp(nvram_safe_get(name),value);}
 """
 # Actual request entry uses events' wait-time metadata; fixture has no generic events.
 template=template.replace('u64 event_mask,event_unmask;','u64 event_mask,event_unmask;unsigned int max_time;').replace('events_desc[]={{NULL,0,0}}','events_desc[]={{NULL,0,0,0}}')
 # Place stubs after types/helpers/apply, before complete request function.
 template+=whole_stubs+'\n#pragma GCC diagnostic push\n#pragma GCC diagnostic ignored "-Wunused-parameter"\n'+update+'\n#pragma GCC diagnostic pop\n'
 main=(here/'guest-persistence-main.c.inc').read_text()
 main=main.replace('assert(validate_asp_apply(NULL,band,&plan,&modern)==1);','assert(update_variables_ex(0,NULL,0,NULL)==0);')
 # start_apply.htm runs update -> commit -> notify in the same request. Replay
 # must happen after that complete sequence, not between update and notification.
 main=main.replace('count=writes;assert(update_variables_ex(0,NULL,0,NULL)==0);assert(writes==count);','count=writes;')
 main=main.replace(' asus_nvram_commit(0,NULL,0,NULL);ej_notify_services(0,NULL,0,NULL);assert(commits==', ' assert(update_variables_ex(0,NULL,0,NULL)==0);assert(writes==count);\n asus_nvram_commit(0,NULL,0,NULL);ej_notify_services(0,NULL,0,NULL);assert(commits==')

 template+=main
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

 # Exercise complete actual server dispatcher with controlled auth/body/output hooks.
 begin=server.index('static void\nhandle_request(');end=server.index('\n}',begin)+2
 http_fixture=(here/'guest-http-fixture.c.inc').read_text().replace('/* ACTUAL_HANDLE_REQUEST */',server[begin:end])
 (root/'http-fixture.c').write_text(http_fixture)
 subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(root/'http-fixture.c'),'-o',str(root/'http-fixture')],check=True)
 subprocess.run([str(root/'http-fixture')],check=True)
 # Actual marked body callback and corrected existing CGI parser, not substitutes.
 begin=source.index('static void\ndo_html_apply_post(');end=source.index('\n}',begin)+2
 body=source[begin:end]
 begin=source.index('void wr_modern_body_clear(void)');end=source.index('\n}',begin)+2
 clear=source[begin:end]
 cgi=(root/'trunk/user/httpd/cgi.c').read_text()
 body_fixture=(here/'guest-body-fixture.c.inc').read_text().replace('/* ACTUAL_CGI */',cgi).replace('/* ACTUAL_INPUT */',body).replace('/* ACTUAL_CLEAR */',clear)
 (root/'body-fixture.c').write_text(body_fixture)
 subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(root/'body-fixture.c'),'-o',str(root/'body-fixture')],check=True)
 subprocess.run([str(root/'body-fixture')],check=True)
 from guest_endpoint_fixture import endpoint_fixture
 joined=endpoint_fixture(template,server,source,cgi,here)
 (root/'endpoint-fixture.c').write_text(joined)
 subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(root/'trunk/user/httpd'),str(root/'endpoint-fixture.c'),'-o',str(root/'endpoint-fixture')],check=True)
 result=subprocess.run([str(root/'endpoint-fixture')],check=True,capture_output=True,text=True)
 responses=[json.loads(line) for line in result.stdout.splitlines() if line.startswith('{')]
 assert len(responses)==77
 assert {r['state'] for r in responses}=={'configuration_matches','reload_required','busy','rejected','unconfirmed','unavailable'}
 for reply in responses:
  assert reply['schemaVersion']==1 and reply['runtimeVerified'] is False and reply['automaticRetry'] is False
  assert set(reply)=={'schemaVersion','state','settingsMayHaveChanged','ramConfigurationMatches','flashCommit','serviceNotification','runtimeVerified','automaticRetry','nextAction'}
  assert reply['nextAction']=='reload_configuration'
  assert reply['ramConfigurationMatches'] is (reply['state']=='configuration_matches')
  assert reply['flashCommit'] in {'not_requested','manual_mode','requested_unverified'}
  assert reply['serviceNotification'] in {'not_requested','requested_unverified'}
  if reply['state'] in {'rejected','reload_required','busy','unavailable'}:assert reply['settingsMayHaveChanged'] is False
  if reply['state']=='unconfirmed':assert reply['settingsMayHaveChanged'] is True

  assert 'endpoint-new-key' not in json.dumps(reply) and 'guest24-password' not in json.dumps(reply)
 subprocess.run(['node',str(here/'check_guest_client.js'),'--actual-replies'],input=json.dumps(responses),text=True,check=True)
 print('PASS actual JSON Guest route:77 parsed replies, match/reload/busy/rejected/unconfirmed, fresh no-op and stale replay, no runtime/flash acceptance or secret echo')
 print(result.stdout.splitlines()[-1])

 if '--browser-check' in sys.argv:
  from check_guest_browser import run_browser
  browser_report=run_browser(joined,server,root,here,sys.argv[1])
  print(json.dumps(browser_report,ensure_ascii=False))

 scratch_bytes=sum(f.stat().st_size for f in root.rglob('*') if f.is_file() and not f.is_symlink())
 scratch_files=sum(1 for f in root.rglob('*') if f.is_file() and not f.is_symlink())
 print('Owned candidate scratch inventory before automatic cleanup:',scratch_files,'files,',scratch_bytes,'bytes')
assert not root.exists()
print('Candidate scratch absent after cleanup')
