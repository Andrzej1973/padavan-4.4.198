"""Private resume pump; owning components injected, no mailbox or device actions."""
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
static int begin_ok=1,prepared,active,finish_ok,take_ok,begins,handoffs,continues,finishes,takes;
int wr_iot_restart_restore_begin(struct wr_iot_restart_restore*s,const unsigned char*id){begins++;s->owner=getpid();memcpy(s->open_id,id,16);s->generation.origin.desired.enabled=1;return begin_ok;}
int wr_iot_restart_restore_step(struct wr_iot_restart_restore*s){assert(s->owner==getpid());return prepared;}
int wr_iot_restart_restore_handoff(struct wr_iot_restart_restore*s,const struct wr_iot_control_request*r){assert(r->created==10&&r->request.enabled==1&&!strcmp(r->id,"07000000000000000000000000000000"));handoffs++;s->phase=WR_RESTORE_HANDOFF;return 0;}
enum wr_iot_result_state wr_iot_activation_continue(const char*id,unsigned long long created){assert(created==10&&!strcmp(id,"07000000000000000000000000000000"));continues++;return active?WR_IOT_RESULT_APPLIED:WR_IOT_RESULT_RECOVERY;}
int wr_iot_restart_restore_rebind_current(struct wr_iot_restart_restore*s){assert(s->phase==WR_RESTORE_HANDOFF);return active;}
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore*s){finishes++;if(finish_ok)s->phase=WR_RESTORE_FINISHED;return finish_ok;}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent*out){takes++;out->restart=1;return take_ok;}
static int shutdown_begins,shutdown_steps;
int wr_iot_rc_quiesce_shutdown_begin(struct wr_iot_rc_quiesce*q,const struct wr_iot_control_request*r){assert(!r->request.enabled&&!r->request.password[0]);shutdown_begins++;q->owner=getpid();return 1;}
int wr_iot_rc_quiesce_advance(struct wr_iot_rc_quiesce*q,struct wr_iot_driver_closed_result*c){assert(q->owner==getpid());shutdown_steps++;*c=(struct wr_iot_driver_closed_result){2,2,3,4};q->complete=1;return 1;}
static int cancel_ok,cancels,preopen_ok;
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){(void)g;return 0;}
int wr_iot_rc_physical_resume_cancel(struct wr_iot_restart_restore*s,const struct wr_iot_rc_quiesce*q){assert((q&&q->complete)||(!q&&preopen_ok));cancels++;if(cancel_ok)s->phase=WR_RESTORE_CANCELLED;return cancel_ok;}
int wr_iot_restart_restore_preopen_rejected(struct wr_iot_restart_restore*s){(void)s;return preopen_ok;}
#include "restart-resume.c"
int main(void){
 struct wr_iot_restart_resume s={0};unsigned char id[16]={7};wr_iot_rc_shutdown.active=1;
 assert(!wr_iot_restart_resume_begin(&s,id,0)&&!s.owner&&!begins);
 assert(wr_iot_restart_resume_begin(&s,id,10)&&begins==1);
 assert(!wr_iot_restart_resume_begin(&s,id,10)&&begins==1);
 assert(!wr_iot_restart_resume_step(&s)&&!handoffs);prepared=1;
 assert(!wr_iot_restart_resume_step(&s)&&handoffs==1&&s.phase==WR_RESUME_REBIND);
 assert(!wr_iot_restart_resume_step(&s)&&handoffs==1&&continues==1&&!finishes);
 active=1;assert(!wr_iot_restart_resume_step(&s)&&s.phase==WR_RESUME_FINISH&&continues==2);
 assert(!wr_iot_restart_resume_step(&s)&&finishes==1&&!takes);
 finish_ok=1;assert(!wr_iot_restart_resume_step(&s)&&finishes==2&&takes==1&&s.restore.phase==WR_RESTORE_FINISHED);
 take_ok=1;assert(wr_iot_restart_resume_step(&s)&&finishes==2&&takes==2);
 assert(wr_iot_restart_resume_step(&s)&&finishes==2&&takes==2&&handoffs==1);
 struct wr_iot_restart_resume refused={0};begin_ok=0;
 assert(!wr_iot_restart_resume_begin(&refused,id,10)&&refused.phase==WR_RESUME_RETAINED);
 int before=begins;assert(!wr_iot_restart_resume_step(&refused)&&begins==before);
 struct wr_iot_restart_resume cancel={0};begin_ok=prepared=1;
 assert(wr_iot_restart_resume_begin(&cancel,id,10));assert(!wr_iot_restart_resume_step(&cancel)&&cancel.phase==WR_RESUME_REBIND);
 struct wr_iot_control_request off={.id="08000000000000000000000000000000",.created=11};strcpy(off.request.password,"must-not-copy");
 assert(!wr_iot_restart_resume_shutdown(&cancel,&off));wr_iot_rc_shutdown.pending=SIGTERM;
 assert(wr_iot_restart_resume_shutdown(&cancel,&off)&&cancel.phase==WR_RESUME_SHUTDOWN&&!cancel.stop_input.request.password[0]);
 assert(!wr_iot_restart_resume_shutdown(&cancel,&off));
 int old_finishes=finishes,old_takes=takes;
 assert(!wr_iot_restart_resume_step(&cancel)&&shutdown_begins==1&&!shutdown_steps);
 assert(!wr_iot_restart_resume_step(&cancel)&&shutdown_steps==1&&cancel.phase==WR_RESUME_SHUTDOWN_CLOSED);
 assert(!wr_iot_restart_resume_step(&cancel)&&shutdown_steps==1&&finishes==old_finishes&&takes==old_takes);
 cancel_ok=1;take_ok=0;
 assert(!wr_iot_restart_resume_step(&cancel)&&cancel.restore.phase==WR_RESTORE_CANCELLED&&cancels==2);
 take_ok=-1;assert(wr_iot_restart_resume_step(&cancel)==-1&&cancels==2);
 assert(wr_iot_restart_resume_step(&cancel)==-1&&cancels==2);
 struct wr_iot_restart_resume preopen={0};wr_iot_rc_shutdown.pending=0;begin_ok=prepared=1;
 assert(wr_iot_restart_resume_begin(&preopen,id,10));assert(!wr_iot_restart_resume_step(&preopen));
 wr_iot_rc_shutdown.pending=SIGTERM;assert(wr_iot_restart_resume_shutdown(&preopen,&off));preopen_ok=1;
 int old_shutdowns=shutdown_begins;
 assert(!wr_iot_restart_resume_step(&preopen)&&preopen.phase==WR_RESUME_SHUTDOWN_ROLLBACK&&!preopen.shutdown.owner&&shutdown_begins==old_shutdowns);
 assert(wr_iot_restart_resume_step(&preopen)==-1&&preopen.phase==WR_RESUME_CANCELLED&&shutdown_begins==old_shutdowns);
 puts("PASS resume pump: one handoff despite uncertain admission, retained backend continuation, finish failure retry, completed cleanup never repeated while terminal take retries, DONE stable, begin refusal retained; owner actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-resume-check-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
