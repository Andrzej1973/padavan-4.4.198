from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include "restart-guest-controller.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int main_ok=1,desired=1,policy_ok=1,state,reads_ok=1,ups,downs;
static enum wr_iot_restart_up_result result;
int wr_iot_restart_main_lan_step(struct wr_iot_restart_main*m){assert(m);return main_ok;}
int wr_iot_rc_restart_guest_policy(int*out){*out=desired;return policy_ok;}
enum wr_iot_restart_up_result wr_iot_restart_guest_up(void){ups++;return result;}
enum wr_iot_restart_up_result wr_iot_restart_guest_down(void){downs++;return WR_RESTART_UP_UNCERTAIN;}
int wr_iot_restart_guest_admin_state(int*out){*out=state;return reads_ok;}
#include "restart-guest-bridge.h"
static int attached,isolated,adds,isolation_ok=1;
int wr_iot_rc_restart_guest_isolation_policy(int*out){*out=1;return 1;}
enum wr_iot_main_bridge_result wr_iot_restart_guest_bridge_attach(void){adds++;attached=1;return WR_MAIN_BRIDGE_UNCERTAIN;}
int wr_iot_restart_guest_bridge_current(void){return attached;}
int wr_iot_restart_guest_isolation_prepare(int v){assert(v==1&&!state&&attached);if(isolation_ok)isolated=1;return isolation_ok;}
int wr_iot_restart_guest_isolation_current(int v){assert(v==1);return isolated;}
#include "restart-guest-controller.c"
int main(void){
 struct wr_iot_restart_main m={0};wr_iot_rc_shutdown.active=1;
 for(int outcome=0;outcome<3;outcome++){
  struct wr_iot_restart_guest s={0};downs=ups=adds=attached=isolated=state=0;result=outcome;desired=1;
  main_ok=0;assert(!wr_iot_restart_guest_begin(&s,&m)&&!s.owner&&!ups);main_ok=1;
  assert(wr_iot_restart_guest_begin(&s,&m)&&s.phase==WR_GUEST_BRIDGE&&!ups);
  assert(!wr_iot_restart_guest_step(&s)&&s.phase==WR_GUEST_ISOLATE&&adds==1&&!ups);
  isolation_ok=0;assert(!wr_iot_restart_guest_step(&s)&&!ups&&s.phase==WR_GUEST_ISOLATE);isolation_ok=1;
  assert(!wr_iot_restart_guest_step(&s)&&s.phase==WR_GUEST_OPEN&&isolated&&!ups);
  isolated=0;assert(!wr_iot_restart_guest_step(&s)&&!ups);isolated=1;
  assert(!wr_iot_restart_guest_step(&s)&&ups==1);
  if(outcome==WR_RESTART_UP_NOT_SUBMITTED){state=1;assert(!wr_iot_restart_guest_step(&s)&&ups==1);continue;}
  state=1;assert(wr_iot_restart_guest_step(&s)&&s.phase==WR_GUEST_ADMIN_UP);
  desired=0;assert(!wr_iot_restart_guest_step(&s)&&ups==1);desired=1;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_guest_step(&s));wr_iot_rc_shutdown.pending=0;
  assert(!wr_iot_restart_guest_step(&s)&&ups==1&&adds==1&&downs==1&&s.phase==WR_GUEST_RECOVER_DOWN);
  reads_ok=0;state=0;assert(!wr_iot_restart_guest_step(&s)&&s.phase==WR_GUEST_RECOVER_DOWN&&downs==1);
  reads_ok=1;assert(!wr_iot_restart_guest_step(&s)&&s.phase==WR_GUEST_DOWN_OBSERVED&&downs==1);
  state=1;assert(!wr_iot_restart_guest_step(&s)&&downs==1&&ups==1&&s.phase==WR_GUEST_RECOVER_DOWN);
 }
 /* Independently exercise each post-UP invalidation, not just policy drift. */
 for(int fault=0;fault<4;fault++){
  struct wr_iot_restart_guest s={0};desired=main_ok=policy_ok=reads_ok=isolation_ok=1;
  state=attached=isolated=ups=downs=adds=0;result=WR_RESTART_UP_RETURNED;
  assert(wr_iot_restart_guest_begin(&s,&m));
  assert(!wr_iot_restart_guest_step(&s));assert(!wr_iot_restart_guest_step(&s));
  assert(!wr_iot_restart_guest_step(&s));state=1;assert(wr_iot_restart_guest_step(&s));
  if(fault==0)main_ok=0;
  if(fault==1)wr_iot_rc_shutdown.pending=SIGTERM;
  if(fault==2)reads_ok=0;
  if(fault==3)attached=0;
  assert(!wr_iot_restart_guest_step(&s)&&downs==1&&s.phase==WR_GUEST_RECOVER_DOWN);
  main_ok=reads_ok=attached=1;wr_iot_rc_shutdown.pending=0;state=0;
  assert(!wr_iot_restart_guest_step(&s)&&downs==1&&s.phase==WR_GUEST_DOWN_OBSERVED);
 }
 struct wr_iot_restart_guest off={0};desired=0;state=0;ups=0;
 assert(wr_iot_restart_guest_begin(&off,&m)&&off.phase==WR_GUEST_POLICY_OFF&&!ups);
 assert(wr_iot_restart_guest_step(&off));state=1;assert(!wr_iot_restart_guest_step(&off)&&!ups);
 puts("PASS Guest controller ordered DOWN bridge/isolation/UP: isolation failure blocks OPEN, single bridge/UP attempt, policy OFF no mutation, uncertain admin readback, Main/policy/pending gates; adapters injected, one-shot DOWN recovery and failed readback covered; routed firewall not claimed");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-guest-controller-') as d:
 p=Path(d)/'check.c';p.write_text(code);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
