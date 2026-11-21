from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "restart-resume.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
#include "restart-resume-retire.c"
int main(void){
 for(int cancelled=0;cancelled<2;cancelled++){
  struct wr_iot_restart_resume s={0};s.owner=s.restore.owner=getpid();
  s.restore.generation.phase=WR_RESTART_GEN_COMMITTED;
  s.phase=cancelled?WR_RESUME_CANCELLED:WR_RESUME_DONE;
  s.restore.phase=cancelled?WR_RESTORE_CANCELLED:WR_RESTORE_FINISHED;
  strcpy(s.stop_input.request.password,"private-copy");
  wr_iot_rc_shutdown.active=1;assert(!wr_iot_restart_resume_retire(&s));wr_iot_rc_shutdown.active=0;
  s.restore.multicast.main=&s.restore.main;assert(!wr_iot_restart_resume_retire(&s));s.restore.multicast.main=NULL;
  s.restore.multicast.guest=&s.restore.guest;assert(!wr_iot_restart_resume_retire(&s));s.restore.multicast.guest=NULL;
  s.restore.multicast.busy=1;assert(!wr_iot_restart_resume_retire(&s));s.restore.multicast.busy=0;
  s.restore.iapp=(struct wr_iot_iapp_child){.owner=getpid(),.attempted=1,.fd=-1,.result=-2};
  assert(!wr_iot_restart_resume_retire(&s));s.restore.iapp=(struct wr_iot_iapp_child){0};
  s.restore.main.generation=&s.restore.generation;assert(!wr_iot_restart_resume_retire(&s));s.restore.main.generation=NULL;
  s.restore.generation.profile.files.saved[3].data=(unsigned char*)1;assert(!wr_iot_restart_resume_retire(&s));s.restore.generation.profile.files.saved[3].data=NULL;
  s.shutdown.active=1;assert(!wr_iot_restart_resume_retire(&s));s.shutdown.active=0;
  s.restore.phase=WR_RESTORE_HANDOFF;assert(!wr_iot_restart_resume_retire(&s));s.restore.phase=cancelled?WR_RESTORE_CANCELLED:WR_RESTORE_FINISHED;
  assert(wr_iot_restart_resume_retire(&s));struct wr_iot_restart_resume zero={0};assert(!memcmp(&s,&zero,sizeof(s)));
  assert(!wr_iot_restart_resume_retire(&s));
 }
 struct wr_iot_restart_resume tail={.owner=getpid(),.phase=WR_RESUME_WAN};
 tail.restore.owner=getpid();tail.restore.phase=WR_RESTORE_FINISHED;tail.restore.generation.phase=WR_RESTART_GEN_COMMITTED;
 assert(!wr_iot_restart_resume_retire(&tail));
 tail.restore.generation.profile.active=1;assert(!wr_iot_restart_resume_retire_for_off(&tail));tail.restore.generation.profile.active=0;
 struct wr_iot_restart_resume explicit_off=tail;explicit_off.phase=WR_RESUME_DONE;
 assert(wr_iot_restart_resume_retire_for_off(&explicit_off)&&!explicit_off.owner&&tail.owner);
 wr_iot_rc_shutdown.normal_route_requested=SIGTERM;
 tail.restore.generation.profile.active=1;assert(!wr_iot_restart_resume_retire(&tail));tail.restore.generation.profile.active=0;
 tail.terminal.fence.level=1;assert(!wr_iot_restart_resume_retire(&tail));tail.terminal.fence.level=0;
 tail.terminal.child=&tail.restore.iapp;assert(!wr_iot_restart_resume_retire(&tail));tail.terminal.child=NULL;
 assert(wr_iot_restart_resume_retire(&tail)&&!tail.owner);wr_iot_rc_shutdown.normal_route_requested=0;
 puts("PASS resume retirement: DONE/CANCELLED proof or routed released WAN handoff without DONE, live admission/pointer/heap/child/fence refusal, volatile wipe and duplicate refusal; completion observer actor");
}
'''
prepared='#define WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED 1\n'+code
prepared=prepared.replace('#include "restart-resume-retire.c"', 'static int completion_ok,checks;\nint wr_iot_restart_restore_completed_current(struct wr_iot_restart_restore*r){assert(r->phase==WR_RESTORE_FINISHED);checks++;return completion_ok;}\n#include "restart-resume-retire.c"')
prepared=prepared.replace('  assert(wr_iot_restart_resume_retire(&s));', '  int before=checks;completion_ok=0;\n  if(!cancelled){assert(!wr_iot_restart_resume_retire(&s)&&s.owner);assert(checks==before+1);}\n  completion_ok=1;assert(wr_iot_restart_resume_retire(&s));\n  assert(checks==before+(cancelled?0:2));')
prepared=prepared.replace(' assert(wr_iot_restart_resume_retire_for_off(&explicit_off)&&!explicit_off.owner&&tail.owner);', ' completion_ok=0;int off_checks=checks;assert(wr_iot_restart_resume_retire_for_off(&explicit_off)&&!explicit_off.owner&&tail.owner&&checks==off_checks);')
prepared=prepared.replace(' assert(wr_iot_restart_resume_retire(&tail)&&!tail.owner);', ' completion_ok=0;int before=checks;assert(wr_iot_restart_resume_retire(&tail)&&!tail.owner&&checks==before);')
with tempfile.TemporaryDirectory(prefix='wr-resume-retire-') as d:
 p=Path(d)/'test.c';b=Path(d)/'test'
 for source in (code,prepared):
  p.write_text(source)
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True)
