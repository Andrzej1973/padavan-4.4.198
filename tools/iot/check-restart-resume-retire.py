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
  s.restore.main.generation=&s.restore.generation;assert(!wr_iot_restart_resume_retire(&s));s.restore.main.generation=NULL;
  s.restore.generation.profile.files.saved[3].data=(unsigned char*)1;assert(!wr_iot_restart_resume_retire(&s));s.restore.generation.profile.files.saved[3].data=NULL;
  s.shutdown.active=1;assert(!wr_iot_restart_resume_retire(&s));s.shutdown.active=0;
  s.restore.phase=WR_RESTORE_HANDOFF;assert(!wr_iot_restart_resume_retire(&s));s.restore.phase=cancelled?WR_RESTORE_CANCELLED:WR_RESTORE_FINISHED;
  assert(wr_iot_restart_resume_retire(&s));struct wr_iot_restart_resume zero={0};assert(!memcmp(&s,&zero,sizeof(s)));
  assert(!wr_iot_restart_resume_retire(&s));
 }
 puts("PASS terminal resume retirement: only consumed DONE/CANCELLED, admission/live pointer/heap/active OFF refusal, volatile wipe of entire context, duplicate refusal; no driver/resource operations");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-resume-retire-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
