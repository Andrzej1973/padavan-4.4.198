"""Scoped one-shot multicast policy controller with owner/transport actors."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#include <assert.h>
#include <signal.h>
#include "restart-multicast-controller.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int required=1,enabled=1,guest=1,owners=1,fail,reads_ok=1,calls;
int wr_iot_restart_main_lan_step(struct wr_iot_restart_main*m){assert(m);return owners;}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest*g){assert(g);return owners;}
int wr_iot_rc_restart_multicast_policy(struct wr_iot_multicast_policy*p){*p=(struct wr_iot_multicast_policy){required,enabled,guest};return 1;}
int wr_iot_restart_multicast_apply(unsigned b,int e){assert(b==(unsigned)calls&&e==enabled);calls++;return !fail;}
int wr_iot_restart_multicast_current(unsigned b,int e){assert(b<2&&e==enabled);return reads_ok;}
int main(void){
 struct wr_iot_restart_main m={0};struct wr_iot_restart_guest g={0};
 g.main=&m;wr_iot_rc_shutdown.active=1;
 for(int off=0;off<2;off++){
  struct wr_iot_multicast s={0};guest=!off;calls=0;
  assert(wr_iot_restart_multicast_begin(&s,&m,&g));
  enabled=0;assert(!wr_iot_restart_multicast_step(&s)&&!calls);enabled=1;
  owners=0;assert(!wr_iot_restart_multicast_step(&s)&&!calls);owners=1;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_multicast_step(&s)&&!calls);wr_iot_rc_shutdown.pending=0;
  for(int i=0;i<(guest?2:1);i++)assert(!wr_iot_restart_multicast_step(&s));
  assert(wr_iot_restart_multicast_step(&s)&&calls==(guest?2:1));
  reads_ok=0;assert(!wr_iot_restart_multicast_step(&s));reads_ok=1;
  assert(wr_iot_restart_multicast_step(&s));
 }
 struct wr_iot_multicast s={0};calls=0;guest=1;fail=1;
 assert(wr_iot_restart_multicast_begin(&s,&m,&g));assert(!wr_iot_restart_multicast_step(&s)&&calls==1&&s.phase==WR_MC_UNCERTAIN);
 fail=0;for(int i=0;i<3;i++)assert(!wr_iot_restart_multicast_step(&s)&&calls==1);
 s=(struct wr_iot_multicast){0};required=0;calls=0;
 assert(wr_iot_restart_multicast_begin(&s,&m,&g)&&wr_iot_restart_multicast_step(&s)&&!calls);
}
'''
with tempfile.TemporaryDirectory(prefix='wr-multicast-controller-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),str(here/'restart-multicast-controller.c'),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True,timeout=15)
print('PASS multicast controller: captured policy/Main/Guest/pending gates, fixed ordered one-shot BSS attempts, Guest OFF omission, no conversion with snoop, readback drift refusal and uncertainty never replayed; owners/transport injected')
