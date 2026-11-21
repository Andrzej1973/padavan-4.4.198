"""Actual terminal service fence/controller with child actor and real SIGTERM."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <signal.h>
#include <unistd.h>
#include "restart-terminal-iapp.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int held,guard_ok=1,launches,receipt,signals;
int wr_iot_service_guard_enter(int e){assert(e==1);if(!guard_ok)return 0;held++;return 1;}
void wr_iot_service_guard_leave(int t){assert(t==1&&held==1);held--;}
int wr_iot_iapp_child_begin(struct wr_iot_iapp_child*s){assert(held&&wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);launches++;s->owner=getpid();s->attempted=1;s->fd=9;return 1;}
int wr_iot_iapp_child_step(struct wr_iot_iapp_child*s){if(receipt){s->fd=-1;s->result=receipt;}return receipt;}
static void shutdown_handler(int sig){if(wr_iot_rc_shutdown_note(sig))return;assert(!held&&!wr_iot_rc_shutdown.active);signals++;}
int main(void){
 struct sigaction sa={0};sa.sa_handler=shutdown_handler;sigemptyset(&sa.sa_mask);assert(!sigaction(SIGTERM,&sa,0));
 for(int scenario=0;scenario<3;scenario++){
  struct wr_iot_terminal_iapp s={0};struct wr_iot_iapp_child child={0};receipt=0;int old_launches=launches;
  assert(wr_iot_terminal_iapp_begin(&s,&child));assert(!wr_iot_terminal_iapp_begin(&s,&child));
  if(scenario==0){assert(!kill(getpid(),SIGTERM));assert(wr_iot_terminal_iapp_step(&s)==-1&&launches==old_launches&&!held&&!s.child);continue;}
  assert(!wr_iot_terminal_iapp_step(&s)&&launches==old_launches+1);
  if(scenario==1)assert(!kill(getpid(),SIGTERM));
  receipt=-2;assert(!wr_iot_terminal_iapp_step(&s)&&held&&!wr_iot_iapp_child_closed(&child));
  /* Separate modeled pending child after testing unknown retention. */
  child.result=0;child.fd=9;receipt=scenario==1?-1:1;
  assert(wr_iot_terminal_iapp_step(&s)==receipt&&!held&&!s.child);
  assert(wr_iot_terminal_iapp_step(&s)==receipt&&launches==old_launches+1);
 }
 assert(signals==2);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-terminal-iapp-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-terminal-iapp.c'),str(here/'radio-stop-fence.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS terminal IAPP actual service fence: prelaunch shutdown cancels, existing child drains under SIGTERM, unknown retains guard, cleanup before signal replay, one launch, stable terminal; child actor injected')
