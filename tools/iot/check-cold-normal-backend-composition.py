"""Actual cold parent and same backend through routed normal OFF and RELEASE.
Hardware/SDK calls remain fixture observations; no device acceptance.
"""
from pathlib import Path
import re,subprocess,tempfile,sys
here=Path(__file__).resolve().parent
source=(here/'check-normal-shutdown-backend-composition.py').read_text()
ns={'__file__':str(here/'check-normal-shutdown-backend-composition.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<normal backend setup>','exec'),ns)
normal=ns['body']
source=(here/'check-rc-cold-terminal.py').read_text()
cold_ns={'__file__':str(here/'check-rc-cold-terminal.py')}
exec(compile(source[:source.index('\nwith tempfile.TemporaryDirectory(')],'<cold owner setup>','exec'),cold_ns)
cold=cold_ns['body'].split('int main(int argc',1)[0]
cold=cold.replace('#include "check-cold-normal-consumer.h"','')
cold+='\n#include "cold-on-root.h"\n#include "rc-cold-route-handoff.inc"\n'
def remove(code,name):
 m=re.search(r'(?m)^(?:static )?(?:int|void|long|unsigned int|enum \w+) '+re.escape(name)+r'\([^;{}]*\)\s*\{',code);assert m,name
 end=m.end();level=1
 while level:
  if code[end]=='{':level+=1
  if code[end]=='}':level-=1
  end+=1
 return code[:m.start()]+code[end:]
for name in ['wr_iot_service_guard_dup','wr_iot_service_guard_enter','wr_iot_service_guard_leave','wr_iot_start_runner_begin','wr_iot_activation_owner_continue','wr_iot_activation_owner_observed']:cold=remove(cold,name)
cold=cold.replace('struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;','extern struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;')
cold=cold.replace('static int depth,down=1,generator_calls,partial;','int *cold_shared_depth(void);\n#define depth (*cold_shared_depth())\nstatic int down=1,generator_calls,partial;')
cold=cold.replace('static struct wr_iot_activation_owner backend;','struct wr_iot_activation_owner *cold_shared_backend(void);\n#define backend (*cold_shared_backend())')
a=cold.index('static int fail_release_unmask;');b=cold.index('#undef sigprocmask',a)+len('#undef sigprocmask');cold=cold[:a]+cold[b:]
# Keep cold Main generation4 -> generation5 hardware observation.
cold=cold.replace('wr_iot_precreated_profile(in,out,"IoT","iot-password",0)','wr_iot_precreated_profile(in,out,saved_ssid,saved_password,0)')
cold=cold.replace('if(lose_active_after_wan)active_proof=0;','assert(!lose_active_after_wan);')
cold=cold.replace('#include "activation-owner.h"','#include "activation-owner.h"\n#include "activation-observe.h"')
cold+='''\n/* Disabled/recovery paths are outside this enabled completion fixture. */\nint wr_iot_cold_disabled_begin(struct wr_iot_cold_disabled * arg0,struct wr_iot_cold_owner * arg1){(void)arg0;(void)arg1;assert(0);return 0;}\nint wr_iot_cold_disabled_current(struct wr_iot_cold_disabled * arg0){(void)arg0;assert(0);return 0;}\nint wr_iot_cold_disabled_release_begin(struct wr_iot_cold_disabled_release * arg0,struct wr_iot_cold_disabled * arg1){(void)arg0;(void)arg1;assert(0);return 0;}\nint wr_iot_cold_disabled_release_current(struct wr_iot_cold_disabled_release * arg0){(void)arg0;assert(0);return 0;}\nint wr_iot_rc_cold_disabled_parent_release(struct wr_iot_cold_disabled_parent_release * arg0,struct wr_iot_cold_disabled_release * arg1){(void)arg0;(void)arg1;assert(0);return 0;}\nint wr_iot_rc_cold_disabled_terminal_begin(struct wr_iot_cold_disabled_terminal * arg0,struct wr_iot_cold_disabled_parent_release * arg1){(void)arg0;(void)arg1;assert(0);return 0;}\nint wr_iot_rc_cold_disabled_terminal_step(struct wr_iot_cold_disabled_terminal * arg0){(void)arg0;assert(0);return 0;}\nint wr_iot_rc_cold_disabled_terminal_retire(struct wr_iot_cold_disabled_terminal * arg0){(void)arg0;assert(0);return 0;}\nint wr_iot_cold_root_preup_recover(struct wr_iot_cold_root * arg0){(void)arg0;assert(0);return 0;}\nint wr_iot_cold_root_shutdown(struct wr_iot_cold_root * arg0,const struct wr_iot_control_request * arg1){(void)arg0;(void)arg1;assert(0);return 0;}\nint wr_iot_rc_cold_root_final_shutdown(struct wr_iot_cold_root * arg0,const struct wr_iot_control_request * arg1){(void)arg0;(void)arg1;assert(0);return 0;}\n#include "cold-on-root-signal.c"\n#include "cold-on-root.c"\n'''
cold+=r'''
void cold_shared_consumer_spent(int);
static struct wr_iot_cold_root full_root;
struct wr_iot_cold_root *cold_full_prepare(const struct wr_iot_control_request *input,const char *dir){
 (void)check;(void)guard;(void)guard_after;(void)begins;(void)continues;(void)claim;(void)active_proof;
 snprintf(profile_path,sizeof(profile_path),"%s/cold-profile",dir);desired=input->request;
 strcpy(saved_ssid,desired.ssid);strcpy(saved_password,desired.password);strcpy(saved_enabled,"1");
 make_profile();up_result=WR_RESTART_UP_RETURNED;
 assert(wr_iot_cold_root_begin(&full_root,input,1));
 int ready=0,refused_release=0;
 for(int i=0;i<160;i++){
  if(full_root.phase==WR_COLD_ROOT_RELEASE&&!refused_release){
   cold_shared_consumer_spent(1);
   assert(!wr_iot_cold_root_step(&full_root)&&full_root.phase==WR_COLD_ROOT_RELEASE);
   assert(full_root.parent.owner==getpid()&&full_root.parent.admission.profile.active&&
    !full_root.released.released&&!wr_iot_rc_shutdown.normal_route_armed);
   cold_shared_consumer_spent(0);refused_release=1;
  }
  assert(!wr_iot_cold_root_step(&full_root));
  if(full_root.phase==WR_COLD_ROOT_TERMINAL_BEGIN){ready=1;break;}
 }
 assert(ready&&refused_release&&up_calls==1&&guest_ups==1&&backend.phase==WR_IOT_OWNER_ACTIVE);
 assert(full_root.released.released&&wr_iot_rc_shutdown.normal_route_armed&&!depth);
 assert(full_root.owner==getpid()&&!full_root.parent.owner&&!full_root.handoff.owner);
 return &full_root;
}
int cold_full_step(void){return wr_iot_cold_root_step(&full_root)==-1;}
void cold_full_cleanup(void){assert(!unlink(profile_path));}
'''
a=normal.index('static void routed_signal');b=a
normal=normal[:a]+'''#include "cold-on-root.h"
struct wr_iot_activation_owner *cold_shared_backend(void){return &backend;}
int *cold_shared_depth(void){return &depth;}
void cold_shared_consumer_spent(int spent){assert(!normal_shutdown.owner);normal_shutdown.spent=spent!=0;}
struct wr_iot_cold_root *cold_full_prepare(const struct wr_iot_control_request *,const char *);
int cold_full_step(void);void cold_full_cleanup(void);
'''+normal[b:]
a=normal.index(' submit(&on);wr_iot_rc_shutdown.radio_off_owned=1;');b=normal.index(' assert(signal(SIGTERM,routed_signal)',a)
normal=normal[:a]+' on.created=wr_iot_control_now();assert(on.created);\n struct wr_iot_cold_root *root=cold_full_prepare(&on,mailbox_directory);\n assert(root->owner==getpid()&&backend.phase==WR_IOT_OWNER_ACTIVE);\n'+normal[b:]
a=normal.index(' normal_entropy=1;assert(');b=normal.index(' off.created=on.created+1;',a)
normal=normal[:a]+''' normal_entropy=1;assert(wr_iot_rc_shutdown.normal_route_armed&&!raise(SIGTERM)&&!shutdowns);
 assert(!wr_iot_rc_normal_shutdown_step()&&!normal_shutdown.generated);
 struct wr_iot_activation_owner backend_before_cold_transfer=backend;
 normal_shutdown.spent=1;assert(!cold_full_step()&&root->owner==getpid());normal_shutdown.spent=0;
 live_epoch++;assert(!cold_full_step()&&root->owner==getpid());live_epoch--;
 assert(!memcmp(&backend_before_cold_transfer,&backend,sizeof(backend))&&wr_iot_rc_shutdown.radio_on_owned);
 assert(cold_full_step()&&!root->owner&&!wr_iot_rc_shutdown.radio_on_owned);
 assert(!memcmp(&backend_before_cold_transfer,&backend,sizeof(backend))&&!depth);
'''+normal[b:]
normal=normal.replace('  assert(!unlink(path));','  assert(!unlink(path)||errno==ENOENT); /* no user mailbox request in cold startup */')
normal=normal.replace(' assert(!rmdir(mailbox_directory));',' cold_full_cleanup();assert(!rmdir(mailbox_directory));')
# Get original common declarations used by actual backend fixture.
cursor=ns
while 'prefix' not in cursor:cursor=cursor['ns']
prefix=cursor['prefix']
prefix=prefix.replace('#include "check-start-staging-composition.c"', '#define wr_iot_driver_initial_idle_read cold_control_idle_read\n#include "check-start-staging-composition.c"\n#undef wr_iot_driver_initial_idle_read\nint wr_iot_driver_initial_idle_read(const unsigned char *n,struct wr_iot_idle_result *r){int ok=cold_control_idle_read(n,r);if(ok)r->epoch=5;return ok;}')
for old,new in [('{1,2','{5,2'),('adapter_epoch==1','adapter_epoch==5'),('epoch==1','epoch==5'),('epoch!=1','epoch!=5'),('live_epoch=1','live_epoch=5')]:
 prefix=prefix.replace(old,new);normal=normal.replace(old,new)
with tempfile.TemporaryDirectory(prefix='wr-full-cold-backend-') as d:
 root=Path(d);subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 for n in ['rc-cold-detach.inc','rc-cold-release.inc','rc-cold-route-handoff.inc']:
  content=(here/n).read_text()
  if n=='rc-cold-release.inc':content=content.replace(' wr_iot_rc_normal_shutdown_arm_commit();',' wr_iot_rc_normal_shutdown_arm_commit();\n if(TEST_CLEANUP_SIGNAL)assert(!raise(SIGTERM)); /* test-only blocked cleanup signal */')
  (root/n).write_text(content)
 (root/'cold.c').write_text(cold);(root/'normal.c').write_text(prefix+'\n#include "check-reopen-unused.h"\n'+normal)
 flags=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),'-DTEST_IAPP_GATE=1','-DTEST_CLEANUP_SIGNAL='+str(int(sys.argv[1]) if len(sys.argv)>1 else 1)]
 subprocess.run(flags+['-c',d+'/cold.c','-o',d+'/inventory.o'],check=True)
 syms=subprocess.check_output(['nm','--defined-only',d+'/inventory.o'],text=True)
 keep={'cold_full_prepare','cold_full_step','cold_full_cleanup'}
 renames=['-D'+r.split()[2]+'=cold_scope_'+r.split()[2] for r in syms.splitlines() if len(r.split())==3 and r.split()[1]=='T' and r.split()[2] not in keep]
 subprocess.run(flags+renames+['-c',d+'/cold.c','-o',d+'/cold.o'],check=True)
 cursor=ns
 while 'units' not in cursor:cursor=cursor['ns']
 units=cursor['units']
 subprocess.run(flags+[d+'/normal.c',d+'/cold.o',*[str(here/n) for n in units],str(here/'physical-stop-session.c'),str(here/'radio-stop-fence.c'),'-o',d+'/check'],check=True)
 subprocess.run([d+'/check'],check=True,timeout=30)
print('PASS cleanup-signal='+str(int(sys.argv[1]) if len(sys.argv)>1 else 1)+' actual cold root begin/step/start runner/backend/parent release -> routed handoff -> normal OFF/physical RELEASE; SDK/hardware observations actors')
