from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
code=r'''#include <assert.h>
#include <stdio.h>
#include "restart-services.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int main_ok=1,policy_ok=1,calls,drift;
static enum wr_iot_restart_service_result outcome=WR_SERVICE_RETURNED;
int wr_iot_restart_main_lan_step(struct wr_iot_restart_main*m){assert(m);return main_ok;}
int wr_iot_rc_restart_service_policy(struct wr_iot_restart_service_policy*p){p->enterprise=1;p->kick_rssi=-75+drift;p->assoc_rssi=-80;return policy_ok;}
enum wr_iot_restart_service_result wr_iot_rc_restart_service_submit(const struct wr_iot_restart_service_policy*p,unsigned slot){assert(p->enterprise&&slot==(unsigned)calls);calls++;return outcome;}
#include "restart-services.c"
int main(void){
 struct wr_iot_restart_main m={0};wr_iot_rc_shutdown.active=1;
 for(int fault=0;fault<3;fault++){
  struct wr_iot_restart_services s={0};calls=0;outcome=fault;
  assert(wr_iot_restart_services_begin(&s,&m));
  drift=1;assert(!wr_iot_restart_services_step(&s)&&!calls&&!s.attempted);drift=0;
  assert(!wr_iot_restart_services_step(&s)&&calls==1);
  if(outcome!=WR_SERVICE_RETURNED){
   for(int i=0;i<4;i++)assert(!wr_iot_restart_services_step(&s)&&calls==1&&s.phase==WR_SERVICES_UNCERTAIN);
   continue;
  }
  main_ok=0;assert(!wr_iot_restart_services_step(&s)&&calls==1);main_ok=1;
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_restart_services_step(&s)&&calls==1);wr_iot_rc_shutdown.pending=0;
  assert(!wr_iot_restart_services_step(&s)&&calls==2);
  assert(!wr_iot_restart_services_step(&s)&&calls==3);
  assert(wr_iot_restart_services_step(&s)&&calls==3&&s.attempted==7);
  policy_ok=0;assert(!wr_iot_restart_services_step(&s)&&calls==3);policy_ok=1;
  assert(wr_iot_restart_services_step(&s)&&calls==3);
 }
 puts("PASS retained service sequence: three ordered one-shot slots, pre-call attempt mark, uncertain/not-submitted never replayed, policy/Main/pending refusal, submitted observation only; SDK actors injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-services-') as d:
 p=Path(d)/'test.c';p.write_text(code);b=Path(d)/'test'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(b)],check=True)
 subprocess.run([str(b)],check=True)
