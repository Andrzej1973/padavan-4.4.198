#!/usr/bin/env python3
"""Actual runner/admission/stage/snapshot/post-OPEN CLOSE rollback; driver/netdev hooks injected."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-start-closed-rollback-composition.c').read_text().split('int main(void){',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('int wr_iot_open_controller_recovery_read(', 'int wr_iot_close_controller_begin(', 'int wr_iot_close_controller_advance(')))+'\n'
close_fixture=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
prefix+=close_fixture
body=r'''
#include "start-runner.h"
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const unsigned char*nonce){assert(a->staged&&r->enabled&&nonce);n->phase=WR_IOT_NET_READY;n->attempted=127;bridge_index=7;rollback_dns=1;return 1;}
int wr_iot_open_controller_submit(struct wr_iot_open_controller*s,const char*id,const struct wr_iot_request*r){assert(id&&r);s->owner=getpid();s->attempt=(struct wr_iot_driver_attempt){{1,2},{1}};s->phase=WR_IOT_OPEN_RECOVERY;return 0;}
int wr_iot_start_commit_step(struct wr_iot_start_commit*s,struct wr_iot_start_admission*a,const struct wr_iot_start_network*n,const struct wr_iot_open_controller*o,const struct wr_iot_request*r){(void)s;(void)a;(void)n;(void)o;(void)r;assert(0);return 0;}
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop*s,const struct wr_iot_driver_attempt*a){(void)s;(void)a;assert(0);return 0;}
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop*s){(void)s;assert(0);return 0;}
int wr_iot_open_controller_recovery_read(const struct wr_iot_open_controller*s,struct wr_iot_driver_open_recovery_result*r){assert(s->owner==getpid());*r=(struct wr_iot_driver_open_recovery_result){1,2,3};return 1;}
int main(void){
 assert(candidate_read(NULL,"wr_iot_enable"));
 struct wr_iot_control_request input={.id="01010101010101010101010101010101",.created=1,.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 for(int failure=0;failure<=0;failure++){
  struct wr_iot_start_runner s={0};reset();idle_reads=0;rollback_dns=0;abort_calls=0;closes=progresses=releases=0;close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  char baseline[9][128];for(unsigned i=0;i<9;i++)strcpy(baseline[i],values[7+i].value);
  assert(wr_iot_start_runner_begin(&s,&input,1,1,0)&&depth==1);
  fail_write=failure;assert(wr_iot_start_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
  fail_write=0;
  while(s.phase!=WR_IOT_RUN_CLOSE||s.close.close.phase!=WR_IOT_CLOSE_UNCERTAIN)
   assert(wr_iot_start_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
  assert(closes==1&&bridge_index==7&&depth==1&&s.admission.snapshot.active);
  progress_result=WR_IOT_DRIVER_CLOSE_PENDING;
  for(unsigned retry=0;retry<3;retry++){
   assert(wr_iot_start_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
   assert(closes==1&&bridge_index==7&&depth==1&&s.admission.snapshot.active);
  }
  progress_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  assert(wr_iot_start_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
  release_result=WR_IOT_DRIVER_CLOSE_PENDING;
  for(unsigned retry=0;retry<3;retry++){
   assert(wr_iot_start_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
   assert(closes==1&&bridge_index==7&&depth==1&&s.admission.snapshot.active);
  }
  release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  wr_iot_rc_shutdown.pending=SIGTERM;
  enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
  for(unsigned i=0;i<35&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_start_runner_step(&s);
  assert(result==WR_IOT_RESULT_REJECTED&&!depth&&!s.admission.snapshot.active&&s.open.phase==WR_IOT_OPEN_RECOVERY&&abort_calls==1&&closes==1&&progresses==4&&releases==4);
  for(unsigned i=0;i<9;i++)assert(!strcmp(baseline[i],values[7+i].value));
  assert(wr_iot_rc_shutdown.pending==SIGTERM);
 }
 puts("PASS actual startup runner/admission/stage/snapshot/post-OPEN rollback: uncertain OPEN then one CLOSE and delayed progress/release retain bridge/baseline/guard before rollback restores exact baseline and releases guard; network/driver hooks injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-runner-close-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('start-runner.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
