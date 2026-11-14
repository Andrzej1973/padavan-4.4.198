from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <fcntl.h>
#include "restart-main-controller.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int calls,probe_ok=1,profile_ok=1;static unsigned long long epoch=2;
static enum wr_iot_restart_up_result outcome;
int wr_iot_service_guard_dup(void){return open("/dev/null",O_RDONLY);}
int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation*g){return g->owner==getpid();}
int wr_iot_restart_generation_step(struct wr_iot_restart_generation*g){assert(!g->main_may_have_started);return 1;}
enum wr_iot_restart_up_result wr_iot_restart_main_up(void){calls++;return outcome;}
int wr_iot_restart_profile_current(const struct wr_iot_request*r){assert(r);return profile_ok;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request*p,const unsigned char*i,struct wr_iot_driver_identity*r){assert(p->epoch==1&&i[0]==7);*r=(struct wr_iot_driver_identity){epoch,3};return probe_ok;}
#define wr_iot_generated_matches(expected,path) ((void)(expected),(void)(path),1)
#include "restart-main-controller.c"
int main(void){
 for(int n=0;n<3;n++){
  struct wr_iot_restart_generation g={.owner=getpid(),.phase=WR_RESTART_GEN_VERIFIED,.profile={.active=1},.origin={.physical={.epoch=1,.generation=3}}};
  struct wr_iot_restart_main s={0};unsigned char id[16]={7};calls=0;outcome=n;wr_iot_rc_shutdown.active=1;
  struct wr_iot_restart_main unchanged=s;unsigned char zero[16]={0};
  assert(!wr_iot_restart_main_begin(&s,&g,zero)&&!calls&&!memcmp(&s,&unchanged,sizeof(s)));
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_restart_main_begin(&s,&g,id)&&!calls&&!g.main_may_have_started);
  wr_iot_rc_shutdown.pending=0;
  g.owner++;assert(!wr_iot_restart_main_begin(&s,&g,id)&&!calls);g.owner=getpid();
  assert(wr_iot_restart_main_begin(&s,&g,id)==(n==WR_RESTART_UP_RETURNED));assert(calls==1&&g.main_may_have_started);
  assert(!wr_iot_restart_main_begin(&s,&g,id)&&calls==1);
  if(n==WR_RESTART_UP_NOT_SUBMITTED){assert(!wr_iot_restart_main_step(&s)&&calls==1);continue;}
  probe_ok=0;assert(!wr_iot_restart_main_step(&s));probe_ok=1;
  profile_ok=0;assert(!wr_iot_restart_main_step(&s));profile_ok=1;
  assert(wr_iot_restart_main_step(&s)&&s.identity.adapter_epoch==2&&calls==1);
  epoch=3;assert(!wr_iot_restart_main_step(&s));epoch=2;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_main_step(&s));wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_restart_main_step(&s)&&calls==1);
 }
 puts("PASS Main controller: UP once, uncertain waits fresh probe, foreign epoch/profile/pending refusal, restoration fence monotonic; generation/transport/probes injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-main-controller-') as d:
 p=Path(d)/'check.c';p.write_text(code);out=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(out)],check=True)
 subprocess.run([str(out)],check=True)
