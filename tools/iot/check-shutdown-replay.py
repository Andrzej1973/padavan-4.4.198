"""First normal signal survives route-clear/disarm and failed stock replay."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <signal.h>
static int replay_raise(int);
#define raise replay_raise
#include "rc-shutdown-admission.h"
#undef raise
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int failures,opposite;
static volatile sig_atomic_t stock;
static int replay_raise(int sig){
 if(failures){failures--;return -1;}
 if(opposite){opposite=0;assert(!raise(SIGQUIT));}
 return raise(sig);
}
static void handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(sig==SIGTERM&&!wr_iot_rc_shutdown.normal_route_armed);
 assert(!wr_iot_rc_shutdown.normal_route_requested&&wr_iot_rc_shutdown.replay_delivered);
 stock++;
}
int main(void){
 struct sigaction sa={0};sa.sa_handler=handler;sigemptyset(&sa.sa_mask);
 assert(!sigaction(SIGTERM,&sa,0)&&!sigaction(SIGQUIT,&sa,0));
 assert(wr_iot_rc_shutdown_route_arm());assert(!raise(SIGTERM));
 assert(wr_iot_rc_shutdown.normal_route_requested==SIGTERM);
 /* Actual final-handoff publication order, with real signals in each gap. */
 wr_iot_rc_shutdown.replay_signal=SIGTERM;
 assert(!raise(SIGQUIT)&&!raise(SIGTERM)&&!stock);
 wr_iot_rc_shutdown.normal_route_requested=0;
 assert(!raise(SIGQUIT)&&!raise(SIGTERM)&&!stock);
 wr_iot_rc_shutdown.normal_route_armed=0;
 assert(!raise(SIGQUIT)&&!raise(SIGTERM)&&!stock);
 wr_iot_rc_shutdown.replay_ready=1;
 assert(!raise(SIGQUIT)&&!stock);
 assert(!wr_iot_rc_shutdown_begin()&&!wr_iot_rc_shutdown_route_arm());
 failures=1;assert(!wr_iot_rc_shutdown_replay_step()&&!stock);
 assert(wr_iot_rc_shutdown_replay_pending());
 opposite=1;assert(wr_iot_rc_shutdown_replay_step()&&stock==1);
 assert(!wr_iot_rc_shutdown_replay_pending());
 assert(!raise(SIGTERM)&&!raise(SIGQUIT)&&stock==1);
 assert(!wr_iot_rc_shutdown_replay_step()&&stock==1);
 assert(!wr_iot_rc_shutdown_note(SIGPWR)&&!wr_iot_rc_shutdown_note(SIGSEGV));
}
'''
for variant in ('term','quit'):
 code=body if variant=='term' else body.replace('SIGTERM','WR_TEST_SWAP').replace('SIGQUIT','SIGTERM').replace('WR_TEST_SWAP','SIGQUIT')
 with tempfile.TemporaryDirectory(prefix='wr-shutdown-replay-'+variant+'-') as d:
  p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
  subprocess.run([str(b)],check=True,timeout=10)
print('PASS actual signal admission replay TERM/QUIT: signals at publication/clear/disarm/ready, failed raise retry, opposite signal at replay, stock once, later duplicates suppressed, faults unchanged; process boundaries injected')
