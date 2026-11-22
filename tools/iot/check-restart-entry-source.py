from pathlib import Path
import subprocess,tempfile,json
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-entry-source-') as d:
 root=Path(d);rc=root/'trunk/user/rc';(rc/'wr-iot').mkdir(parents=True)
 (root/'iot-iapp-policy-source.json').write_text(json.dumps({'board':'WR1200JS','production_ready':False,'iapp_compile_gate_enabled':True}))
 (rc/'wr-iot/restart-iapp-policy.h').write_text('#define WR_IOT_IAPP_POLICY_PREPARED 1\n')
 (rc/'wr-iot/radio-entry-result.h').write_bytes((here/'radio-entry-result.h').read_bytes())
 (rc/'net_wifi.c').write_text('static int legacy,wr_iot_last_stop_result;\nstruct wr_iot_radio_stop_fence {int unused;};\nstatic int wr_iot_radio_stop_fence_begin(struct wr_iot_radio_stop_fence*f){(void)f;return 1;}\nvoid\nrestart_wifi_rt(int radio_on, int need_reload_conf)\n{\n struct wr_iot_radio_stop_fence wr_iot_fence={0};\n if(!wr_iot_radio_stop_fence_begin(&wr_iot_fence)){wr_iot_last_stop_result=0;return;}\n (void)radio_on;(void)need_reload_conf;legacy++;\n}\n')
 (rc/'wr-iot-rc-backend.c').write_text('enum {WR_IOT_OWNER_IDLE,WR_IOT_OWNER_INITIAL_OFF,OTHER};\nstruct wr_iot_activation_owner {int phase,busy;};struct wr_iot_rebind_owner {int owner;};\nstatic struct wr_iot_activation_owner backend;\nstatic struct wr_iot_rebind_owner rebind;\n')
 (rc/'Makefile').write_text('OBJS=wr-iot-restart-scheduler.o\n')
 cmd=['python3','-B',str(here/'prepare-restart-entry-source.py'),str(root)]
 originals={p:p.read_bytes() for p in (rc/'net_wifi.c',rc/'wr-iot-rc-backend.c',rc/'Makefile')}
 netpath=rc/'net_wifi.c';outside=root/'external.c';outside.write_bytes(originals[netpath]);netpath.unlink();netpath.symlink_to(outside)
 assert subprocess.run(cmd,capture_output=True).returncode and outside.read_bytes()==originals[netpath]
 netpath.unlink();netpath.write_bytes(originals[netpath])
 for path in originals:
  path.write_text('changed anchor\n')
  before={p:p.read_bytes() for p in originals}
  assert subprocess.run(cmd,capture_output=True).returncode
  assert before=={p:p.read_bytes() for p in originals}
  assert not (root/'iot-restart-entry-source.json').exists() and not (rc/'wr-iot-restart-entry.c').exists()
  path.write_bytes(originals[path])
 netpath.write_text(originals[netpath].decode().replace('wr_iot_radio_stop_fence_begin(&wr_iot_fence)','missing_fence(&wr_iot_fence)'))
 assert subprocess.run(cmd,capture_output=True).returncode
 assert not (root/'iot-restart-entry-source.json').exists()
 netpath.write_bytes(originals[netpath])
 subprocess.run(cmd,check=True)
 subprocess.run(['python3','-B',str(here/'check-restart-entry-manifest.py'),str(root)],check=True)
 net=(rc/'net_wifi.c').read_text();back=(rc/'wr-iot-rc-backend.c').read_text()
 assert net.index('WR_IOT_PRIVATE_RESTART_ENTRY')<net.index('legacy++')
 code='#define BOARD_WR1200JS\n#include <assert.h>\nstatic inline void logmessage(const char *tag,const char *fmt,...){assert(tag&&fmt);}\n#include "wr-iot/restart-entry.h"\nstatic int claimed,entry_result,on_entry_calls,off_entry_result,initial_result;\nenum wr_iot_radio_entry_result wr_iot_initial_restart_entry(int on,int reload){assert(reload==1);return on?(enum wr_iot_radio_entry_result)initial_result:WR_RADIO_ENTRY_NATIVE;}\nenum wr_iot_radio_entry_result wr_iot_radio_off_entry(int on,int reload){assert(reload==1);return on?WR_RADIO_ENTRY_NATIVE:(enum wr_iot_radio_entry_result)off_entry_result;}\nenum wr_iot_radio_entry_result wr_iot_radio_on_entry(int on,int reload){if(!on)return WR_RADIO_ENTRY_NATIVE;assert(on==1&&reload==1);on_entry_calls++;return (enum wr_iot_radio_entry_result)entry_result;}\nenum wr_iot_radio_entry_result wr_iot_restart_entry(int on,int reload){assert((on==0||on==1)&&reload==1);return on?(enum wr_iot_radio_entry_result)claimed:WR_RADIO_ENTRY_NATIVE;}\n'+net+back+r'''
int main(void){
 assert(!wr_iot_rc_restart_owned());backend.phase=WR_IOT_OWNER_INITIAL_OFF;assert(!wr_iot_rc_restart_owned());
 backend.phase=OTHER;assert(wr_iot_rc_restart_owned());backend.phase=WR_IOT_OWNER_IDLE;
 rebind.owner=1;assert(wr_iot_rc_restart_owned());rebind.owner=0;backend.busy=1;assert(wr_iot_rc_restart_owned());
 entry_result=WR_RADIO_ENTRY_OWNED;restart_wifi_rt(1,1);assert(!legacy&&on_entry_calls==1);
 entry_result=WR_RADIO_ENTRY_REFUSED;restart_wifi_rt(1,1);assert(!legacy&&on_entry_calls==2);
 entry_result=WR_RADIO_ENTRY_NATIVE;
 initial_result=WR_RADIO_ENTRY_OWNED;restart_wifi_rt(1,1);assert(!legacy);
 initial_result=WR_RADIO_ENTRY_REFUSED;restart_wifi_rt(1,1);assert(!legacy);
 initial_result=WR_RADIO_ENTRY_NATIVE;
 claimed=WR_RADIO_ENTRY_OWNED;restart_wifi_rt(1,1);assert(!legacy);
 claimed=WR_RADIO_ENTRY_REFUSED;restart_wifi_rt(1,1);assert(!legacy);
 claimed=0;restart_wifi_rt(1,1);assert(legacy==1);
 off_entry_result=WR_RADIO_ENTRY_OWNED;restart_wifi_rt(0,1);assert(legacy==1);
 off_entry_result=WR_RADIO_ENTRY_REFUSED;restart_wifi_rt(0,1);assert(legacy==1);
 off_entry_result=WR_RADIO_ENTRY_NATIVE;restart_wifi_rt(0,1);assert(legacy==2);

}
'''
 p=root/'test.c';p.write_text(code);b=root/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I'+str(rc),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
 # The same generated net_wifi body must remain native when its paired gate
 # is disabled or the board is different; no candidate entry is called.
 inactive=code.split('int main(void){',1)[0]+r'''
int main(void){restart_wifi_rt(1,1);assert(legacy==1&&!on_entry_calls);restart_wifi_rt(0,1);assert(legacy==2&&!on_entry_calls);}
'''
 for other in (False,True):
  (rc/'wr-iot/restart-iapp-policy.h').write_text('#define WR_IOT_IAPP_POLICY_PREPARED '+('1' if other else '0')+'\n')
  p.write_text(inactive.replace('#define BOARD_WR1200JS','#define BOARD_OTHER') if other else inactive)
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-I'+str(rc),str(p),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True,timeout=5)
 (rc/'wr-iot/restart-iapp-policy.h').write_text('#define WR_IOT_IAPP_POLICY_PREPARED 1\n')

 # Compile the actual newly staged entry translation unit, not the hook actor.
 for header in here.glob('*.h'):
  target=rc/'wr-iot'/header.name
  if not target.exists():target.write_bytes(header.read_bytes())
 (rc/'shared-wifi').mkdir(exist_ok=True)
 for header in (here.parent/'shared-wifi').glob('*.h'):
  (rc/'shared-wifi'/header.name).write_bytes(header.read_bytes())
 for name in ['restart-entry','initial-restart-entry']:
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-I'+str(rc),'-c',str(rc/('wr-iot-'+name+'.c')),'-o',str(root/(name+'.o'))],check=True)
 header=rc/'wr-iot/restart-entry.h';saved=header.read_bytes();header.write_bytes(saved.replace(b'enum wr_iot_radio_entry_result wr_iot_restart_entry',b'int wr_iot_restart_entry'))
 assert subprocess.run(['python3','-B',str(here/'check-restart-entry-manifest.py'),str(root)],capture_output=True).returncode
 header.write_bytes(saved)
 original=(rc/'net_wifi.c').read_text();(rc/'net_wifi.c').write_text(original+'// drift\n')
 assert subprocess.run(['python3','-B',str(here/'check-restart-entry-manifest.py'),str(root)],capture_output=True).returncode
 (rc/'net_wifi.c').write_text(original)
 before=(rc/'net_wifi.c').read_bytes();assert subprocess.run(cmd,capture_output=True).returncode and (rc/'net_wifi.c').read_bytes()==before
print('PASS prepared restart hook: claim returns before legacy body, never-opened versus owned predicate, duplicate installer refuses; SDK body/entry actors, full SDK compilation pending')
