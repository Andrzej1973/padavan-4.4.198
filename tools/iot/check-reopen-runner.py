#!/usr/bin/env python3
"""Actual runner/admission/stage/snapshot/post-OPEN CLOSE rollback; driver/netdev hooks injected."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-start-closed-rollback-composition.c').read_text().split('int main(void){',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('int wr_iot_open_controller_recovery_read(', 'int wr_iot_close_controller_begin(', 'int wr_iot_close_controller_advance(')))+'\n'
close_fixture=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith('int wr_iot_bridge_set_up('))+'\n'
prefix+=close_fixture
body=r'''
#include "reopen-admission.h"
#include "reopen-start.h"
#include "reopen-rollback.h"
#include "reopen-network.h"
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const unsigned char*nonce){assert(a->staged&&r->enabled&&nonce);n->phase=WR_IOT_NET_READY;n->attempted=127;bridge_index=7;rollback_dns=0;strcpy(values[8].value,"1");strcpy(values[9].value,"1");return 1;}
int wr_iot_open_controller_submit(struct wr_iot_open_controller*s,const char*id,const struct wr_iot_request*r){assert(id&&r);s->owner=getpid();s->attempt=(struct wr_iot_driver_attempt){{1,2},{1}};s->phase=WR_IOT_OPEN_CONFIRMED;return 1;}
int wr_iot_start_commit_step(struct wr_iot_start_commit*s,struct wr_iot_start_admission*a,const struct wr_iot_start_network*n,const struct wr_iot_open_controller*o,const struct wr_iot_request*r){assert(a&&n&&o&&r);assert(wr_iot_request_snapshot_suspend(&a->snapshot));s->phase=WR_IOT_COMMIT_ACTIVE;return 1;}
int wr_iot_open_controller_recovery_read(const struct wr_iot_open_controller*s,struct wr_iot_driver_open_recovery_result*r){assert(s->owner==getpid());*r=(struct wr_iot_driver_open_recovery_result){1,2,3};return 1;}
int wr_iot_driver_open_recovery_read(const struct wr_iot_driver_attempt*a,struct wr_iot_driver_open_recovery_result*r){assert(a->request_id[0]==1);*r=(struct wr_iot_driver_open_recovery_result){1,2,3};return 1;}
static unsigned network_fault;
int wr_iot_bridge_prepare(const char*g,const char*m,const char*f,const char*l,const struct wr_iot_range*r,size_t n){assert(depth&&g&&m&&f&&l&&!r&&!n);bridge_index=7;return network_fault!=1;}
int wr_iot_quarantine_apply(void){assert(depth&&bridge_index);return network_fault!=2;}
int wr_iot_bridge_attach(void){assert(depth&&bridge_index);return network_fault!=3;}
int wr_iot_bridge_set_up(int up){assert(depth);return !up||network_fault!=4;}
int wr_iot_dns_activation_prepare(void){assert(depth&&bridge_index);rollback_dns=1;return network_fault==6?1:0;}
int wr_iot_policy_enable_current(void){assert(depth&&bridge_index&&rollback_dns);strcpy(values[9].value,"1");return network_fault!=7;}
int wr_iot_network_services_ready(const char*g){assert(depth&&g);return rollback_dns==1;}
int wr_iot_active_filter_ready_current(void){assert(depth);return !strcmp(values[9].value,"1");}
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
  while(s.phase!=WR_IOT_RUN_ACTIVE)(void)wr_iot_start_runner_step(&s);
  assert(!depth&&s.admission.snapshot.active&&!s.admission.snapshot.token);
  struct wr_iot_control_request off={.id="02020202020202020202020202020202",.created=2};
  struct wr_iot_active_stop stop={0};
  assert(wr_iot_active_stop_begin(&stop,&s,&off));
  assert(!wr_iot_active_stop_begin(&stop,&s,&off));
  assert(s.phase==WR_IOT_RUN_STOPPING);
  assert(wr_iot_start_runner_continue(&s,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  unsigned before_closes=closes;
  assert(wr_iot_active_stop_continue(&stop,input.id,off.created)==WR_IOT_RESULT_RECOVERY);
  assert(wr_iot_active_stop_continue(&stop,off.id,off.created+1)==WR_IOT_RESULT_RECOVERY);
  stop.busy=1;
  assert(wr_iot_active_stop_continue(&stop,off.id,off.created)==WR_IOT_RESULT_RECOVERY);
  stop.busy=0;assert(closes==before_closes);
  while(stop.stop.phase!=WR_IOT_STOP_ISOLATE)
   assert(wr_iot_active_stop_continue(&stop,off.id,off.created)==WR_IOT_RESULT_RECOVERY);
  assert(depth==3&&s.admission.snapshot.active&&stop.stop.disable.services.settings.active);
  quarantine_ready=0;unsigned previous_closes=closes;
  for(unsigned retry=0;retry<3;retry++){
   assert(wr_iot_active_stop_continue(&stop,off.id,off.created)==WR_IOT_RESULT_RECOVERY);
   assert(stop.stop.phase==WR_IOT_STOP_ISOLATE&&depth==3&&closes==previous_closes);
   assert(s.admission.snapshot.active&&stop.stop.disable.services.settings.active);
  }
  quarantine_ready=1;
  enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
  for(unsigned i=0;i<55&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_active_stop_continue(&stop,off.id,off.created);
  assert(result==WR_IOT_RESULT_APPLIED&&!depth&&!s.admission.snapshot.active&&s.open.phase==WR_IOT_OPEN_CONFIRMED&&stop.stop.phase==WR_IOT_STOP_COMPLETE&&closes==1&&progresses==1&&releases==1);
  (void)baseline;for(unsigned i=0;i<9;i++)assert(!strcmp(i<3?"0":"",values[7+i].value));
  assert(wr_iot_active_stop_continue(&stop,off.id,off.created)==WR_IOT_RESULT_APPLIED);
  assert(s.phase==WR_IOT_RUN_STOPPED);
  assert(!wr_iot_reopen_closed_current(&s,&stop));
  int reopen_guard=wr_iot_service_guard_enter(1);assert(reopen_guard==1);
  assert(wr_iot_reopen_closed_current(&s,&stop));
  struct wr_iot_reopen_witness witness={0};
  assert(wr_iot_reopen_witness_take(&witness,&s,&stop));
  assert(!wr_iot_reopen_witness_take(&witness,&s,&stop));
  struct wr_iot_reopen_witness original=witness;
  assert(wr_iot_reopen_witness_current(&witness));
  struct wr_iot_start_admission fresh={0};int writes_before_reopen=writes;
  wr_iot_rc_shutdown.pending=SIGTERM;
  assert(!wr_iot_reopen_start_begin(&fresh,&witness)&&!fresh.snapshot.active);
  wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_reopen_start_begin(&fresh,&witness)&&depth==2&&fresh.snapshot.active);
  assert(fresh.admitted&&!fresh.mutation_started&&!fresh.staged&&writes==writes_before_reopen);
  assert(fresh.idle.epoch==witness.attempt.identity.adapter_epoch&&fresh.idle.serial==witness.close_serial);
  assert(!wr_iot_reopen_start_begin(&fresh,&witness));
  unsigned initial_queries_before=idle_reads;
  assert(!wr_iot_start_admission_stage(&fresh,s.nonce,candidate_read,NULL,1,1,0));
  assert(initial_queries_before==idle_reads&&writes==writes_before_reopen);

  assert(wr_iot_start_admission_cancel(&fresh)&&depth==1&&!fresh.snapshot.active);
  for(unsigned fault=0;fault<=7;fault++){
   struct wr_iot_start_runner next={0};
   struct wr_iot_control_request second=input;second.id[0]='2';second.created=3;
   assert(wr_iot_request_read(&second.request,candidate_read,NULL,1,1,0,NULL,0));
   struct wr_iot_start_runner previous=s;struct wr_iot_active_stop previous_stop=stop;
   network_fault=fault;assert(wr_iot_start_runner_begin_reopen(&next,&second,1,1,0,&witness));
   if(fault==5){writes=0;fail_write=8;} /* gate setter injection, other cases cover resource ops */
   enum wr_iot_result_state outcome=WR_IOT_RESULT_RECOVERY;
   for(unsigned budget=0;budget<35&&outcome==WR_IOT_RESULT_RECOVERY;budget++){
    if(next.phase==WR_IOT_RUN_OPEN)wr_iot_rc_shutdown.pending=SIGTERM;
    outcome=wr_iot_start_runner_continue(&next,second.id,second.created);
    if(next.phase==WR_IOT_RUN_PRE_ROLLBACK)fail_write=0;
   }
   fail_write=0;wr_iot_rc_shutdown.pending=0;
   assert(outcome==WR_IOT_RESULT_REJECTED&&depth==1&&!next.admission.snapshot.active);
   assert(!memcmp(&s,&previous,sizeof(s))&&!memcmp(&stop,&previous_stop,sizeof(stop)));
   assert(!next.prior_closed.submitted&&next.open.phase==WR_IOT_OPEN_IDLE);
  }



  bridge_index=7;strcpy(values[8].value,"1");rollback_dns=1;
  assert(!wr_iot_reopen_closed_current(&s,&stop));
  assert(wr_iot_reopen_witness_current(&witness));
  bridge_index=0;strcpy(values[8].value,"0");rollback_dns=0;
  witness.close_serial++;assert(!wr_iot_reopen_witness_current(&witness));witness=original;
  witness.open_token++;assert(!wr_iot_reopen_witness_current(&witness));witness=original;
  witness.submitted=1;assert(!wr_iot_reopen_witness_current(&witness));witness=original;
  witness.owner=0;assert(!wr_iot_reopen_witness_current(&witness));witness=original;
  bss_down=0;assert(!wr_iot_reopen_witness_current(&witness));bss_down=1;
  assert(!memcmp(&witness,&original,sizeof(witness)));

  stop.stop.attempt.request_id[0]^=1;assert(!wr_iot_reopen_closed_current(&s,&stop));stop.stop.attempt.request_id[0]^=1;

  unsigned long long saved_serial=stop.stop.close_serial;
  stop.stop.close_serial++;assert(!wr_iot_reopen_closed_current(&s,&stop));stop.stop.close_serial=saved_serial;
  unsigned long long saved_token=stop.stop.close.request.open_token;
  stop.stop.close.request.open_token++;assert(!wr_iot_reopen_closed_current(&s,&stop));stop.stop.close.request.open_token=saved_token;
  s.admission.snapshot.active=1;assert(!wr_iot_reopen_closed_current(&s,&stop));s.admission.snapshot.active=0;
  for(unsigned field=7;field<16;field++){
   char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"foreign");
   assert(!wr_iot_reopen_closed_current(&s,&stop));strcpy(values[field].value,saved);
  }
  wr_iot_service_guard_leave(reopen_guard);assert(!depth);

  struct wr_iot_request empty={0};assert(!memcmp(&s.input.request,&empty,sizeof(empty)));
  assert(wr_iot_start_runner_continue(&s,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  assert(closes==1&&progresses==1&&releases==1);
  assert(!wr_iot_rc_shutdown.pending);
 }
 puts("PASS actual second startup runner with CLOSED witness: network failures and pre-OPEN cancellation recover without changing old STOPPED owner; no second OPEN submitted, driver/resources injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-reopen-runner-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('reopen-network.c','reopen-rollback.c','reopen-start.c','reopen-admission.c','active-stop.c','start-runner.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','precreated-stop.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
