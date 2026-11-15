"""Root signal/fresh OFF routing with real queued SIGTERM and injected children."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "cold-on-root-signal.h"
#include "cold-on-root-recovery.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int entropy_calls,clock_calls,pre_calls,stop_calls,pre_done,stop_done,claim=1,clock_fault,entropy_fault,pending_fault;
static unsigned char entropy_byte=2;static char captured[33];
static int fake_entropy(void*b,unsigned n,unsigned flags){assert(n==32&&flags==1);entropy_calls++;memset(b,entropy_byte,n);return entropy_fault?31:32;}
#define WR_IOT_GETRANDOM(buf,n,flags) fake_entropy(buf,n,flags)
static int fake_clock(clockid_t id,struct timespec*out){assert(id==CLOCK_MONOTONIC);clock_calls++;out->tv_sec=clock_fault==2?1:8;out->tv_nsec=0;return clock_fault==1?-1:0;}
static int fake_pending(sigset_t*out){return pending_fault?-1:sigpending(out);}
int wr_iot_cold_root_preup_recover(struct wr_iot_cold_root*s){assert(s->owner==getpid());pre_calls++;if(pre_done)memset(s,0,sizeof(*s));return pre_done;}
int wr_iot_cold_root_shutdown(struct wr_iot_cold_root*s,const struct wr_iot_control_request*off){
 assert(s->owner==getpid());stop_calls++;
 if(s->stop.owner||!s->handoff.owner)assert(!off);
 else{
  assert(off&&off->created==8&&strlen(off->id)==32&&!off->request.enabled&&!off->request.password[0]&&!off->request.ssid[0]&&!off->request.gateway[0]);
  strcpy(captured,off->id);if(claim)s->stop.owner=getpid();
 }
 if(stop_done)memset(s,0,sizeof(*s));
 return stop_done;
}
static int final_calls;
int wr_iot_rc_cold_root_final_shutdown(struct wr_iot_cold_root*s,const struct wr_iot_control_request*r){assert(s->phase==WR_COLD_ROOT_TERMINAL);final_calls++;if(r){assert(r->created==8);s->final_off_attempted=1;}return 0;}
#define clock_gettime fake_clock
#define sigpending fake_pending
#include "cold-on-root-signal.c"
#undef sigpending
#undef clock_gettime
static void setup(struct wr_iot_cold_root*s){
 memset(s,0,sizeof(*s));s->owner=getpid();s->enabled=1;s->phase=WR_COLD_ROOT_WAIT;
 s->parent.owner=getpid();s->parent.generation.main_may_have_started=1;
 s->handoff.owner=getpid();s->handoff.parent=&s->parent;s->handoff.attempted=s->handoff.backend_claimed=1;
 s->handoff.created=7;memset(s->handoff.id,'1',32);
 wr_iot_rc_shutdown.active=wr_iot_rc_shutdown.radio_off_owned=1;wr_iot_rc_shutdown.pending=SIGTERM;
 clock_fault=entropy_fault=pending_fault=pre_done=stop_done=0;entropy_byte=2;
}
int main(void){
 struct wr_iot_cold_root s,zero={0};sigset_t blocked,old;int signal_number;
 setup(&s);wr_iot_rc_shutdown.pending=0;assert(wr_iot_cold_root_signal_step(&s)==1&&!entropy_calls&&!stop_calls);
 sigemptyset(&blocked);sigaddset(&blocked,SIGTERM);assert(!sigprocmask(SIG_BLOCK,&blocked,&old));
 assert(!raise(SIGTERM));s.parent.generation.main_may_have_started=0;
 assert(!wr_iot_cold_root_signal_step(&s)&&wr_iot_rc_shutdown.pending==SIGTERM&&pre_calls==1&&!entropy_calls);
 assert(!sigwait(&blocked,&signal_number)&&signal_number==SIGTERM&&!sigprocmask(SIG_SETMASK,&old,NULL));
 pre_done=1;assert(wr_iot_cold_root_signal_step(&s)==-1&&!memcmp(&zero,&s,sizeof(s)));
 for(int fault=0;fault<5;fault++){
  setup(&s);int old_stop=stop_calls;
  if(fault==0)clock_fault=1;
  if(fault==1)clock_fault=2;
  if(fault==2)entropy_fault=1;
  if(fault==3)entropy_byte=0;
  if(fault==4){memset(s.handoff.id,'2',32);entropy_byte=0x22;}
  assert(!wr_iot_cold_root_signal_step(&s)&&stop_calls==old_stop&&s.owner&&!s.stop.owner);
 }
 setup(&s);assert(!wr_iot_cold_root_signal_step(&s)&&s.stop.owner==getpid()&&strlen(captured)==32);
 int calls=entropy_calls,clocks=clock_calls;entropy_fault=clock_fault=1;
 assert(!wr_iot_cold_root_signal_step(&s)&&entropy_calls==calls&&clock_calls==clocks);
 stop_done=1;assert(wr_iot_cold_root_signal_step(&s)==-1&&!memcmp(&zero,&s,sizeof(s))&&entropy_calls==calls);
 setup(&s);s.handoff.owner=0;assert(!wr_iot_cold_root_signal_step(&s)&&entropy_calls==calls);
 setup(&s);s.phase=WR_COLD_ROOT_TERMINAL;int stops=stop_calls;assert(!wr_iot_cold_root_signal_step(&s)&&final_calls==1&&stop_calls==stops&&entropy_calls==calls);
 s.terminal.terminal.shutdown_held=1;s.release.owner=getpid();s.release.created=7;memset(s.release.id,'1',32);s.released.released=1;s.released.release=&s.release;
 wr_iot_rc_shutdown.radio_off_owned=0;wr_iot_rc_shutdown.radio_on_owned=1;
 assert(!wr_iot_cold_root_signal_step(&s)&&s.final_off_attempted&&entropy_calls==calls+1);
 assert(!wr_iot_cold_root_signal_step(&s)&&entropy_calls==calls+1);calls=entropy_calls;
 wr_iot_rc_shutdown.radio_on_owned=0;
 setup(&s);pending_fault=1;assert(!wr_iot_cold_root_signal_step(&s)&&entropy_calls==calls);
 setup(&s);s.handoff.parent=NULL;assert(!wr_iot_cold_root_signal_step(&s)&&entropy_calls==calls);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-root-signal-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=20)
print('PASS cold root signal routing: real blocked SIGTERM noted, pre-UP and prehandoff routes, nonblocking entropy/time failures retained, zero/collision refuse, one captured OFF then no new entropy/time, existing terminal drain; child actors, no public entry')
