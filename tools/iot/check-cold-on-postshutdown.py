"""Actual cold shutdown controller with bound backend/quiesce actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "cold-on-postshutdown.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guest_state=1,guest_downs,rejected,active=1,off_ok=1,off_calls,advances,closed_ok=1;
int wr_iot_cold_guest_step(struct wr_iot_cold_guest*g){assert(g);if(guest_state){guest_downs++;guest_state=0;}return 0;}
int wr_iot_restart_guest_admin_state(int*out){*out=guest_state;return 1;}
int wr_iot_rc_cold_shutdown_rejected(const struct wr_iot_cold_owner*p,const struct wr_iot_cold_handoff*h){assert(p&&h);return rejected;}
int wr_iot_rc_cold_shutdown_advance(const struct wr_iot_cold_owner*p,const struct wr_iot_cold_handoff*h){assert(p&&h);advances++;return active;}
int wr_iot_rc_cold_shutdown_off_begin(const struct wr_iot_cold_owner*p,const struct wr_iot_cold_handoff*h,struct wr_iot_rc_quiesce*off,const struct wr_iot_control_request*r){assert(p&&h&&r->created==8&&!r->request.enabled);off_calls++;if(off_ok)off->owner=getpid();return off_ok;}
int wr_iot_rc_quiesce_advance(struct wr_iot_rc_quiesce*off,struct wr_iot_driver_closed_result*out){assert(off->owner==getpid());*out=(struct wr_iot_driver_closed_result){5,2,7,9};off->complete=1;return 1;}
int wr_iot_rc_cold_shutdown_closed(const struct wr_iot_cold_owner*p,const struct wr_iot_cold_handoff*h,const struct wr_iot_rc_quiesce*off,struct wr_iot_driver_closed_result*out){assert(p&&h&&off);memset(out,0,sizeof(*out));return off->complete&&closed_ok;}
#include "cold-on-postshutdown.c"
int main(void){
 for(int fault=0;fault<4;fault++){
  struct wr_iot_cold_stop s={0};struct wr_iot_cold_owner p={0};struct wr_iot_cold_handoff h={0};struct wr_iot_control_request off={0};
  p.owner=h.owner=getpid();p.guest.owner=getpid();p.guest.main=&p.main;h.parent=&p;h.attempted=h.backend_claimed=1;h.created=7;h.phase=WR_COLD_HANDOFF_WAIT;memset(h.id,'1',32);
  off.created=8;memset(off.id,'2',32);wr_iot_rc_shutdown.active=wr_iot_rc_shutdown.radio_off_owned=1;wr_iot_rc_shutdown.pending=SIGTERM;
  guest_state=1;guest_downs=off_calls=advances=0;rejected=fault==1;off_ok=fault!=2;closed_ok=fault!=3;active=1;
  off.request.password[0]='x';assert(!wr_iot_cold_postshutdown_begin(&s,&p,&h,&off));off.request.password[0]=0;
  assert(wr_iot_cold_postshutdown_begin(&s,&p,&h,&off)&&!wr_iot_cold_postshutdown_begin(&s,&p,&h,&off));
  assert(wr_iot_cold_postshutdown_step(&s)==rejected&&guest_downs==1);
  if(rejected)assert(!off_calls&&s.phase==WR_COLD_STOP_REJECTED);
  else assert(off_calls==1);
  for(int n=0;n<4;n++)assert(wr_iot_cold_postshutdown_step(&s)==(fault==0||fault==1));
  assert(guest_downs==1&&off_calls==(fault!=1)&&p.owner==getpid());
  wr_iot_rc_shutdown.pending=0;assert(!wr_iot_cold_postshutdown_step(&s));
 }
}
'''
with tempfile.TemporaryDirectory(prefix='wr-cold-poststop-') as d:
 p=Path(d)/'check.c';p.write_text(body);b=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS cold post-handoff shutdown controller: owned Guest DOWN, separate rejected/CLOSED paths, one OFF begin, failure retained without replay, fresh CLOSED recheck, pending required; backend/quiesce actors')
