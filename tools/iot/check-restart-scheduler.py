from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <stdio.h>
#include <unistd.h>
#include "restart-resume.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int released,starts,steps,stops,terminal;
static struct wr_iot_restart_resume*owner;
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent*i){i->restart=i->radio_on=1;return released;}
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume*s,const unsigned char*id,unsigned long long created){assert(id[0]&&created);starts++;owner=s;s->owner=getpid();s->phase=WR_RESUME_RESTORE;return 1;}
int wr_iot_restart_resume_step(struct wr_iot_restart_resume*s){assert(s==owner);steps++;if(terminal)s->phase=WR_RESUME_DONE;return terminal;}
int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume*s,const struct wr_iot_control_request*r){assert(s==owner&&!r->request.enabled&&!r->request.password[0]);stops++;return 1;}
int wr_iot_restart_resume_retire(struct wr_iot_restart_resume*s){if(s->phase!=WR_RESUME_DONE)return 0;memset(s,0,sizeof(*s));return 1;}
int wr_iot_rc_physical_preresume_cancel(void){assert(0);return 0;}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent*i){(void)i;assert(0);return 0;}
#include "restart-scheduler.c"
int main(void){
 unsigned char id[16]={7};wr_iot_rc_shutdown.active=1;
 assert(!wr_iot_restart_scheduler_begin(id,10)&&!starts&&!wr_iot_restart_scheduler_pending());released=1;
 assert(wr_iot_restart_scheduler_begin(id,10)&&starts==1&&wr_iot_restart_scheduler_pending());
 assert(!wr_iot_restart_scheduler_begin(id,11)&&starts==1);
 assert(!wr_iot_restart_scheduler_step()&&steps==1);
 assert(!wr_iot_restart_scheduler_shutdown("bad",11)&&!stops);
 assert(wr_iot_restart_scheduler_shutdown("08000000000000000000000000000000",11)&&stops==1);
 assert(!wr_iot_restart_scheduler_retire());terminal=1;
 assert(wr_iot_restart_scheduler_step()&&!wr_iot_restart_scheduler_pending());
 assert(wr_iot_restart_scheduler_retire()&&!resume.owner);
 assert(wr_iot_restart_scheduler_begin(id,12)&&starts==2&&owner==&resume);
 puts("PASS private restart scheduler: exact ready gate, one stable owner, duplicate begin refuses, explicit bounded step, OFF identity only, terminal-only retirement/reuse; owning actors injected, no RC hooks");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-restart-scheduler-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
