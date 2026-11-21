"""Actual held terminal/fence until caller's checked shutdown cleanup."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <signal.h>
#include <unistd.h>
#include "restart-terminal-iapp.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int held,launches,receipt,signals,cleanups,fail_unmask,inject_signal;
int wr_iot_service_guard_enter(int e){assert(e==1);held++;return 1;}
void wr_iot_service_guard_leave(int t){assert(t==1&&held==1);held--;}
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s){assert(held&&!wr_iot_rc_shutdown.pending);launches++;s->owner=getpid();s->attempted=1;s->fd=9;return 1;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){if(inject_signal){inject_signal=0;assert(!raise(SIGTERM));}if(receipt){s->fd=-1;s->result=receipt;}return receipt;}
static int mask_hook(int how,const sigset_t*set,sigset_t*old){if(how==SIG_SETMASK&&fail_unmask)return -1;return sigprocmask(how,set,old);}
#define sigprocmask mask_hook
#include "radio-stop-fence.c"
#undef sigprocmask
struct root {struct wr_iot_terminal_iapp terminal;struct wr_iot_iapp_child child;int proof;};
static struct root *live;
static void shutdown_handler(int sig){
 if(wr_iot_rc_shutdown_note(sig))return;
 assert(!held&&!wr_iot_rc_shutdown.active&&live&&!live->terminal.owner&&!live->child.owner);
 assert(cleanups>signals);signals++;
}
static void parent_cleanup(void*data){struct root*s=data;assert(s==live&&s->proof&&!held&&!s->terminal.guard&&!s->terminal.child);cleanups++;memset(s,0,sizeof(*s));}
int main(void){
 struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,NULL));
 for(int scenario=0;scenario<4;scenario++){
  struct root s={0},before;live=&s;receipt=0;int old_launches=launches,old_signals=signals,old_cleanups=cleanups;
  assert(wr_iot_terminal_iapp_begin(&s.terminal,&s.child));
  assert(!wr_iot_terminal_iapp_shutdown_drain(&s.terminal)&&!s.terminal.shutdown_held);
  if(scenario){assert(!wr_iot_terminal_iapp_step(&s.terminal)&&launches==old_launches+1);}
  if(scenario==3){
   s.terminal.defer_pending_shutdown=1;inject_signal=1;receipt=1;
   assert(!wr_iot_terminal_iapp_step(&s.terminal)&&s.terminal.shutdown_held&&held&&signals==old_signals);
   assert(wr_iot_rc_shutdown.pending==SIGTERM);
  }else assert(!raise(SIGTERM)&&signals==old_signals);
  if(scenario==1||scenario==2){
   receipt=-2;assert(!wr_iot_terminal_iapp_shutdown_drain(&s.terminal)&&held&&s.terminal.shutdown_held);
   assert(!wr_iot_terminal_iapp_shutdown_finish(&s.terminal,parent_cleanup,&s)&&cleanups==old_cleanups);
   /* Unknown evidence cannot be cured by relaunch; model a later known child receipt. */
   s.child.result=0;s.child.fd=9;receipt=scenario==1?1:-1;
  }
  assert(wr_iot_terminal_iapp_shutdown_drain(&s.terminal)&&held&&s.terminal.fence.owner==getpid()&&signals==old_signals);
  assert(!wr_iot_terminal_iapp_step(&s.terminal));
  assert(launches==old_launches+(scenario!=0));
  s.proof=1;before=s;fail_unmask=1;
  assert(!wr_iot_terminal_iapp_shutdown_finish(&s.terminal,parent_cleanup,&s)&&held&&signals==old_signals&&cleanups==old_cleanups);
  assert(!memcmp(&s,&before,sizeof(s)));
  fail_unmask=0;assert(wr_iot_terminal_iapp_shutdown_finish(&s.terminal,parent_cleanup,&s));
  assert(!held&&signals==old_signals+1&&cleanups==old_cleanups+1&&!s.terminal.fence.owner);
  assert(!wr_iot_terminal_iapp_shutdown_finish(&s.terminal,parent_cleanup,&s));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-terminal-shutdown-') as d:
 p=Path(d)/'test.c';p.write_text(body);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-terminal-iapp.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=10)
print('PASS held terminal shutdown actual fence: no new child, known child drains, unknown retains, ordinary step cannot release held fence, failed unmask retains exact state, caller cleanup after guard release before real SIGTERM; parent proof/child actors')
