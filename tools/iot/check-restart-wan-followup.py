from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <signal.h>
#include "restart-wan-followup.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int current_ok=1;
int wr_iot_rc_restart_wan_current(int on,enum wr_iot_wan_followup p){assert(on==1);(void)p;return current_ok;}
static int valid=1,calls;static enum wr_iot_wan_followup plan;static struct wr_iot_wan_followup_state*current;
int wr_iot_rc_restart_wan_plan(int on,enum wr_iot_wan_followup*out){assert(on==1);*out=plan;return valid;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup p){assert(p==plan&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending);calls++;assert(current->attempted&&!wr_iot_wan_followup_step(current));}
int main(void){
 for(plan=WR_WAN_NONE;plan<=WR_WAN_RECONNECT;plan++){
  struct wr_iot_wan_followup_state s={0};current=&s;calls=0;
  assert(!wr_iot_wan_followup_capture(&s,1));wr_iot_rc_shutdown.active=1;
  valid=0;assert(!wr_iot_wan_followup_capture(&s,1)&&!s.owner);valid=1;
  assert(wr_iot_wan_followup_capture(&s,1)&&!wr_iot_wan_followup_capture(&s,1));
  assert(!wr_iot_wan_followup_step(&s)&&!calls);wr_iot_rc_shutdown.active=0;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_wan_followup_step(&s)&&!calls);wr_iot_rc_shutdown.pending=0;
  current_ok=0;assert(!wr_iot_wan_followup_step(&s)&&!s.attempted&&!calls);current_ok=1;
  assert(wr_iot_wan_followup_step(&s)&&calls==(plan!=WR_WAN_NONE));
  assert(wr_iot_wan_followup_step(&s)&&calls==(plan!=WR_WAN_NONE));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-wan-followup-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-I'+str(here),str(p),str(here/'restart-wan-followup.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=5)
print('PASS deferred WAN controller: captured under admission, blocked while active/pending, fixed plan dispatch once after caller release, reentrant/duplicate no replay; SDK actors, terminal take caller proof still required')
