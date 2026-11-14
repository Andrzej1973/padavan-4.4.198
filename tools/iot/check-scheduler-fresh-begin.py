"""Fresh private resume identity gate; actual scheduler, owner actor injected."""
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
static int ready,radio_on=1,clock_ok=1,entropy_count=32,zero,entropy_calls,begins,retain;
static int test_entropy(void*b,unsigned n,unsigned f){assert(n==32&&f==1);entropy_calls++;memset(b,zero?0:9,n);return entropy_count;}
static int test_clock(clockid_t c,struct timespec*t){assert(c==CLOCK_MONOTONIC);t->tv_sec=20;t->tv_nsec=0;return clock_ok?0:-1;}
#define WR_IOT_GETRANDOM(b,n,f) test_entropy(b,n,f)
#define clock_gettime test_clock
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent*i){i->restart=1;i->radio_on=radio_on;return ready;}
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume*s,const unsigned char*id,unsigned long long created){for(unsigned i=0;i<16;i++)assert(id[i]==9);assert(created==20);begins++;s->owner=getpid();s->phase=retain?WR_RESUME_RETAINED:WR_RESUME_RESTORE;return !retain;}
int wr_iot_restart_resume_step(struct wr_iot_restart_resume*s){(void)s;return 0;}
int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume*s,const struct wr_iot_control_request*r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_restart_resume_retire(struct wr_iot_restart_resume*s){(void)s;return 0;}
#include "restart-scheduler.c"
int main(void){
 assert(!wr_iot_restart_scheduler_begin_fresh()&&!entropy_calls&&!begins);
 wr_iot_rc_shutdown.active=1;assert(!wr_iot_restart_scheduler_begin_fresh()&&!entropy_calls);
 ready=1;radio_on=0;assert(!wr_iot_restart_scheduler_begin_fresh()&&!entropy_calls);radio_on=1;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_scheduler_begin_fresh()&&!entropy_calls);wr_iot_rc_shutdown.pending=0;
 clock_ok=0;assert(!wr_iot_restart_scheduler_begin_fresh()&&!entropy_calls);clock_ok=1;
 entropy_count=15;assert(!wr_iot_restart_scheduler_begin_fresh()&&!begins&&!resume.owner);
 entropy_count=32;zero=1;assert(!wr_iot_restart_scheduler_begin_fresh()&&!begins);zero=0;
 retain=1;assert(!wr_iot_restart_scheduler_begin_fresh()&&begins==1&&wr_iot_restart_scheduler_pending());
 int calls=entropy_calls;assert(!wr_iot_restart_scheduler_begin_fresh()&&begins==1&&entropy_calls==calls);
 /* Actor-only reset supplies a separate success scenario, never production retirement. */
 memset(&resume,0,sizeof(resume));retain=0;assert(wr_iot_restart_scheduler_begin_fresh()&&begins==2);
 assert(!wr_iot_restart_scheduler_begin_fresh()&&begins==2);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-scheduler-fresh-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS fresh resume identity: RELEASE/radio/admission before entropy, clock/short-read/zero-ID refusal before owner, exact identity/time, retained failed begin prevents replay; owner/entropy actors injected')
