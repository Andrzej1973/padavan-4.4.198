#!/usr/bin/env python3
"""Actual initial OFF plus NVRAM observation; driver/BSS/DNS hooks injected."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
body=r'''
#define WR_IOT_START_FIXTURE_NO_MAIN 1
#define wr_iot_driver_initial_idle_read fixture_initial_idle_read
#include "check-start-staging-composition.c"
#undef wr_iot_driver_initial_idle_read
#include "initial-off.h"
static int dns_state;
static unsigned idle_calls,idle_failure;
static int drift_generation;
int wr_iot_driver_initial_idle_read(const unsigned char *nonce,struct wr_iot_idle_result *out){
 idle_calls++;if(idle_failure==idle_calls)return 0;
 int ok=fixture_initial_idle_read(nonce,out);
 if(drift_generation&&idle_calls==2)out->generation++;
 return ok;
}
int wr_iot_dns_activation_recovery_state(void){assert(depth);return dns_state;}
int main(void){
 assert(candidate_read(0,"wr_iot_enable"));reset();
 for(unsigned i=7;i<16;i++)strcpy(values[i].value,i<10?"0":"");
 struct wr_iot_control_request request={.id="01010101010101010101010101010101",.created=1};
 struct wr_iot_initial_off s={0};wr_iot_rc_shutdown.active=1;
 int before_writes=writes;
 for(idle_failure=1;idle_failure<=2;idle_failure++){
  idle_calls=0;idle_reads=0;
  assert(!wr_iot_initial_off_begin(&s,&request)&&!s.owner&&!s.ready&&!depth&&writes==before_writes);
 }
 idle_failure=0;idle_calls=idle_reads=0;drift_generation=1;
 assert(!wr_iot_initial_off_begin(&s,&request)&&!s.owner&&!s.ready&&!depth&&writes==before_writes);
 drift_generation=0;idle_calls=idle_reads=0;
 wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_initial_off_begin(&s,&request)&&!idle_calls);wr_iot_rc_shutdown.pending=0;
 struct wr_iot_control_request zero=request;memset(zero.id,'0',32);assert(!wr_iot_initial_off_begin(&s,&zero)&&!idle_calls);
 assert(wr_iot_initial_off_begin(&s,&request)&&!depth&&s.ready&&idle_reads==2&&writes==before_writes);
 struct wr_iot_initial_off retained=s;
 assert(!wr_iot_initial_off_begin(&s,&request));
 assert(!wr_iot_initial_off_observed(&s));
 int token=wr_iot_service_guard_enter(1);assert(token==1);
 assert(wr_iot_initial_off_observed(&s)&&!memcmp(&s,&retained,sizeof(s)));
 for(unsigned i=7;i<16;i++){
  char saved[128];strcpy(saved,values[i].value);strcpy(values[i].value,"foreign");
  assert(!wr_iot_initial_off_observed(&s));strcpy(values[i].value,saved);
 }
 bridge_index=7;assert(!wr_iot_initial_off_observed(&s));bridge_index=0;
 bss_down=0;assert(!wr_iot_initial_off_observed(&s));bss_down=1;
 dns_state=1;assert(!wr_iot_initial_off_observed(&s));dns_state=0;
 s.idle.epoch++;assert(!wr_iot_initial_off_observed(&s));s=retained;
 s.idle.generation++;assert(!wr_iot_initial_off_observed(&s));s=retained;
 s.idle.serial=~0ULL;assert(!wr_iot_initial_off_observed(&s));s=retained;
 wr_iot_service_guard_leave(token);assert(!depth&&writes==before_writes);
 memset(&s,0,sizeof(s));for(unsigned i=7;i<10;i++)values[i].value[0]=0;
 assert(wr_iot_initial_off_begin(&s,&request)&&!depth&&writes==before_writes);
 puts("PASS actual initial never-opened OFF: double fresh idle, absent/zero gates, empty temp credentials, all9 foreign fields and bridge/BSS/DNS/epoch/generation/serial refusal; no writes, driver/network hooks injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-initial-off-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(body);binary=Path(d)/'check'
 units=('initial-off.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
