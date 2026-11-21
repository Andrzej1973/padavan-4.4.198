from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include "radio-off-wan.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guard=1,depth,observed=1,current=1,calls;
static struct wr_iot_off_wan *active;
int wr_iot_service_guard_enter(int on){assert(on==1&&!depth);if(!guard)return 0;depth=1;return 1;}
void wr_iot_service_guard_leave(int t){assert(t==1&&depth);depth=0;}
int wr_iot_radio_off_observed(const struct wr_iot_physical_stop_request*r){assert(depth&&r->action==WR_STOP_RELEASE);return observed;}
int wr_iot_rc_restart_wan_current(int on,enum wr_iot_wan_followup plan){assert(depth&&!on&&(plan==WR_WAN_NONE||plan==WR_WAN_FULL_RESTART));return current;}
void wr_iot_rc_restart_wan_submit(enum wr_iot_wan_followup plan){assert(!depth&&plan==WR_WAN_FULL_RESTART&&active->attempted);calls++;assert(!wr_iot_off_wan_step(active));}
#include "radio-off-wan.c"
int main(void){
 struct wr_iot_radio_off_owner off={.owner=getpid(),.result=1,.policy_ready=1,.released={WR_STOP_RELEASE,1,2,3,4,5,{1}}};
 for(int full=0;full<2;full++){
  struct wr_iot_off_wan s={0};active=&s;calls=0;off.policy.wan=full?WR_WAN_FULL_RESTART:WR_WAN_NONE;
  assert(!wr_iot_off_wan_begin(&s,&off));wr_iot_rc_shutdown.radio_off_owned=1;
  assert(wr_iot_off_wan_begin(&s,&off));assert(!wr_iot_off_wan_begin(&s,&off));
  observed=0;assert(!wr_iot_off_wan_step(&s)&&!s.attempted&&!calls);observed=1;
  current=0;assert(!wr_iot_off_wan_step(&s)&&!s.attempted);current=1;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_off_wan_step(&s)&&!calls);wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_off_wan_step(&s)&&s.returned&&calls==full&&!depth);
  assert(wr_iot_off_wan_step(&s)&&calls==full);
  wr_iot_rc_shutdown.radio_off_owned=0;
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-off-wan-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS OFF WAN: retained NONE/full plan, fresh DOWN/current checks, guard released before SDK, one attempt/reentrant no replay, pending hold; actors injected, service ordering unbound')
