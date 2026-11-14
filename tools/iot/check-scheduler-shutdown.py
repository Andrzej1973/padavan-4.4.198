"""Actual scheduler sees blocked shutdown; entropy/owner adapters injected."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <signal.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "restart-resume.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int entropy_ok,clock_ok=1,admit,steps,stops,entropy_calls;
static int test_entropy(void*b,unsigned n,unsigned flags){assert(n==32&&flags==1);entropy_calls++;memset(b,8,n);return entropy_ok?32:-1;}
static int test_clock(clockid_t c,struct timespec*t){assert(c==CLOCK_MONOTONIC);t->tv_sec=20;t->tv_nsec=0;return clock_ok?0:-1;}
#define WR_IOT_GETRANDOM(b,n,f) test_entropy(b,n,f)
#define clock_gettime test_clock
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent*i){i->restart=i->radio_on=1;return 1;}
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume*s,const unsigned char*id,unsigned long long created){assert(id[0]);s->owner=getpid();s->created=created;s->phase=WR_RESUME_REBIND;s->restore.phase=WR_RESTORE_HANDOFF;return 1;}
int wr_iot_restart_resume_step(struct wr_iot_restart_resume*s){assert(s->owner==getpid());steps++;return 0;}
int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume*s,const struct wr_iot_control_request*r){assert(r->created==20&&!r->request.enabled&&!r->request.password[0]&&r->id[0]=='0'&&r->id[1]=='8');stops++;if(admit)s->phase=WR_RESUME_SHUTDOWN;return admit;}
int wr_iot_restart_resume_retire(struct wr_iot_restart_resume*s){(void)s;return 0;}
int wr_iot_rc_physical_preresume_cancel(void){assert(0);return 0;}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent*i){(void)i;assert(0);return 0;}
#include "restart-scheduler.c"
int main(void){
 sigset_t block,old,queued;struct timespec zero={0};unsigned char id[16]={7};
 sigemptyset(&block);sigaddset(&block,SIGTERM);assert(!sigprocmask(SIG_BLOCK,&block,&old));
 wr_iot_rc_shutdown.active=1;assert(wr_iot_restart_scheduler_begin(id,10));
 assert(!kill(getpid(),SIGTERM));
 assert(!wr_iot_restart_scheduler_step()&&wr_iot_rc_shutdown.pending==SIGTERM&&!steps&&!stops&&entropy_calls==1);
 entropy_ok=1;clock_ok=0;assert(!wr_iot_restart_scheduler_step()&&!steps&&!stops&&entropy_calls==1);
 clock_ok=1;resume.created=21;assert(!wr_iot_restart_scheduler_step()&&!steps&&!stops&&entropy_calls==1);
 resume.created=10;assert(!wr_iot_restart_scheduler_step()&&!steps&&stops==1);
 admit=1;assert(!wr_iot_restart_scheduler_step()&&steps==1&&stops==2&&resume.phase==WR_RESUME_SHUTDOWN);
 assert(!wr_iot_restart_scheduler_step()&&steps==2&&stops==2);
 assert(!sigpending(&queued)&&sigismember(&queued,SIGTERM)==1);
 assert(sigtimedwait(&block,NULL,&zero)==SIGTERM);assert(!sigprocmask(SIG_SETMASK,&old,NULL));
}
'''
with tempfile.TemporaryDirectory(prefix='wr-scheduler-shutdown-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS actual scheduler blocked SIGTERM observation without consumption; entropy/clock/backward-time/admission failures hold ON progress; accepted shutdown once then OFF pump; owner/entropy adapters injected')
