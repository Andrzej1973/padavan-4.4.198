#!/usr/bin/env python3
"""Actual runner/admission/stage/snapshot/pre-OPEN rollback; netdev hooks injected."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-start-rollback-composition.c').read_text().split('int main(void){',1)[0]
body=r'''
#include "start-runner.h"
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const unsigned char*nonce){assert(a->staged&&r->enabled&&nonce);n->phase=WR_IOT_NET_RECOVERY;return 0;}
int wr_iot_open_controller_submit(struct wr_iot_open_controller*s,const char*id,const struct wr_iot_request*r){(void)s;(void)id;(void)r;assert(0);return 0;}
int wr_iot_start_commit_step(struct wr_iot_start_commit*s,struct wr_iot_start_admission*a,const struct wr_iot_start_network*n,const struct wr_iot_open_controller*o,const struct wr_iot_request*r){(void)s;(void)a;(void)n;(void)o;(void)r;assert(0);return 0;}
int wr_iot_start_close_step(struct wr_iot_start_close*c,const struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o){(void)c;(void)a;(void)o;assert(0);return 0;}
int wr_iot_start_closed_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o,struct wr_iot_start_close*c){(void)b;(void)n;(void)a;(void)o;(void)c;assert(0);return 0;}
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop*s,const struct wr_iot_driver_attempt*a){(void)s;(void)a;assert(0);return 0;}
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop*s){(void)s;assert(0);return 0;}
int main(void){
 assert(candidate_read(NULL,"wr_iot_enable"));
 struct wr_iot_control_request input={.id="01010101010101010101010101010101",.created=1,.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 for(int failure=0;failure<=16;failure++){
  struct wr_iot_start_runner s={0};reset();idle_reads=0;rollback_dns=0;abort_calls=0;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  char baseline[9][128];for(unsigned i=0;i<9;i++)strcpy(baseline[i],values[7+i].value);
  assert(wr_iot_start_runner_begin(&s,&input,1,1,0)&&depth==1);
  fail_write=failure;assert(wr_iot_start_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
  fail_write=0;wr_iot_rc_shutdown.pending=SIGTERM;
  enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
  for(unsigned i=0;i<20&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_start_runner_step(&s);
  assert(result==WR_IOT_RESULT_REJECTED&&!depth&&!s.admission.snapshot.active&&s.open.phase==WR_IOT_OPEN_IDLE&&!abort_calls);
  for(unsigned i=0;i<9;i++)assert(!strcmp(baseline[i],values[7+i].value));
  assert(wr_iot_rc_shutdown.pending==SIGTERM);
 }
 puts("PASS actual startup runner/admission/stage/snapshot/pre-OPEN rollback:16 setter faults plus network refusal restore exact baseline, no OPEN or DNS abort, pending shutdown retained; network/driver hooks injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-runner-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('start-runner.c','start-network-rollback.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
