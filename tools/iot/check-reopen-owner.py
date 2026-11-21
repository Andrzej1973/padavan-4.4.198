#!/usr/bin/env python3
"""Actual runner/admission/stage/snapshot/post-OPEN CLOSE rollback; driver/netdev hooks injected."""
from pathlib import Path
import subprocess,sys,tempfile
here=Path(__file__).resolve().parent
prefix=(here/'check-start-closed-rollback-composition.c').read_text().split('int main(void){',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith(('int wr_iot_open_controller_recovery_read(', 'int wr_iot_close_controller_begin(', 'int wr_iot_close_controller_advance(')))+'\n'
close_fixture=(here/'check-driver-close-controller.c').read_text().split('int main(void)',1)[0]
prefix='\n'.join(line for line in prefix.splitlines() if not line.startswith('int wr_iot_bridge_set_up('))+'\n'
prefix+=close_fixture.replace("out->open_request_id[0]=attempt->request_id[0];", "memcpy(out->open_request_id,attempt->request_id,sizeof(out->open_request_id));")
body=r'''
#include "activation-owner.h"
#include "reopen-admission.h"
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const unsigned char*nonce){assert(a->staged&&r->enabled&&nonce);n->phase=WR_IOT_NET_READY;n->attempted=127;bridge_index=7;rollback_dns=0;strcpy(values[8].value,"1");strcpy(values[9].value,"1");return 1;}
int wr_iot_open_controller_submit(struct wr_iot_open_controller*s,const char*id,const struct wr_iot_request*r){assert(id&&r);s->owner=getpid();s->attempt=(struct wr_iot_driver_attempt){{1,2},{1}};s->phase=WR_IOT_OPEN_CONFIRMED;return 1;}
static int commit_fault;
int wr_iot_start_commit_step(struct wr_iot_start_commit*s,struct wr_iot_start_admission*a,const struct wr_iot_start_network*n,const struct wr_iot_open_controller*o,const struct wr_iot_request*r){assert(a&&n&&o&&r);if(commit_fault)return 0;assert(wr_iot_request_snapshot_suspend(&a->snapshot));s->phase=WR_IOT_COMMIT_ACTIVE;rollback_dns=0;return 1;}
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
  struct wr_iot_activation_owner owner={0};
  struct wr_iot_start_runner *runner=&owner.start;
#define s (*runner)
reset();idle_reads=0;rollback_dns=0;abort_calls=0;closes=progresses=releases=0;close_result=WR_IOT_DRIVER_CLOSE_UNCERTAIN;progress_result=release_result=WR_IOT_DRIVER_CLOSE_CALL_COMPLETED;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  char baseline[9][128];for(unsigned i=0;i<9;i++)strcpy(baseline[i],values[7+i].value);
  struct wr_iot_control_request idle_off={.id="03030303030303030303030303030303",.created=1};
  assert(wr_iot_activation_owner_execute(&owner,&idle_off,1,1,0)==WR_IOT_RESULT_REJECTED&&!depth);
  assert(wr_iot_activation_owner_execute(&owner,&input,1,1,0)==WR_IOT_RESULT_RECOVERY&&depth==1);
  assert(wr_iot_activation_owner_execute(&owner,&input,1,1,0)==WR_IOT_RESULT_RECOVERY);
  fail_write=failure;assert(wr_iot_activation_owner_continue(&owner,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  fail_write=0;
  while(s.phase!=WR_IOT_RUN_ACTIVE)(void)wr_iot_activation_owner_continue(&owner,input.id,input.created);
  assert(!depth&&s.admission.snapshot.active&&!s.admission.snapshot.token);
  struct wr_iot_control_request off={.id="02020202020202020202020202020202",.created=2};

  char owned_value[128];strcpy(owned_value,values[7].value);
  strcpy(values[7].value,"foreign");
  assert(wr_iot_activation_owner_execute(&owner,&off,1,1,0)==WR_IOT_RESULT_REJECTED);
  assert(owner.phase==WR_IOT_OWNER_ACTIVE&&!depth&&!closes);
  strcpy(values[7].value,owned_value);
  assert(wr_iot_activation_owner_execute(&owner,&off,1,1,0)==WR_IOT_RESULT_RECOVERY);
  assert(wr_iot_activation_owner_execute(&owner,&off,1,1,0)==WR_IOT_RESULT_RECOVERY);
  assert(s.phase==WR_IOT_RUN_STOPPING);
  assert(wr_iot_start_runner_continue(&s,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  unsigned before_closes=closes;
  assert(wr_iot_activation_owner_continue(&owner,input.id,off.created)==WR_IOT_RESULT_RECOVERY);
  assert(wr_iot_activation_owner_continue(&owner,off.id,off.created+1)==WR_IOT_RESULT_RECOVERY);
  owner.stop.busy=1;
  assert(wr_iot_activation_owner_continue(&owner,off.id,off.created)==WR_IOT_RESULT_RECOVERY);
  owner.stop.busy=0;assert(closes==before_closes);
  while(owner.stop.stop.phase!=WR_IOT_STOP_ISOLATE)
   assert(wr_iot_activation_owner_continue(&owner,off.id,off.created)==WR_IOT_RESULT_RECOVERY);
  assert(depth==3&&s.admission.snapshot.active&&owner.stop.stop.disable.services.settings.active);
  quarantine_ready=0;unsigned previous_closes=closes;
  for(unsigned retry=0;retry<3;retry++){
   assert(wr_iot_activation_owner_continue(&owner,off.id,off.created)==WR_IOT_RESULT_RECOVERY);
   assert(owner.stop.stop.phase==WR_IOT_STOP_ISOLATE&&depth==3&&closes==previous_closes);
   assert(s.admission.snapshot.active&&owner.stop.stop.disable.services.settings.active);
  }
  quarantine_ready=1;wr_iot_rc_shutdown.pending=SIGTERM;
  enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
  for(unsigned i=0;i<55&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_activation_owner_continue(&owner,off.id,off.created);
  assert(result==WR_IOT_RESULT_APPLIED&&!depth&&!s.admission.snapshot.active&&s.open.phase==WR_IOT_OPEN_CONFIRMED&&abort_calls==0&&owner.stop.stop.phase==WR_IOT_STOP_COMPLETE&&closes==1&&progresses==1&&releases==1);
  (void)baseline;for(unsigned i=0;i<9;i++)assert(!strcmp(i<3?"0":"",values[7+i].value));
  assert(wr_iot_activation_owner_continue(&owner,off.id,off.created)==WR_IOT_RESULT_APPLIED);
  assert(s.phase==WR_IOT_RUN_STOPPED);
  struct wr_iot_request empty={0};assert(!memcmp(&s.input.request,&empty,sizeof(empty)));
  assert(wr_iot_start_runner_continue(&s,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  assert(closes==1&&progresses==1&&releases==1);
  assert(wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.pending==SIGTERM);
  assert(owner.phase==WR_IOT_OWNER_OFF);
  assert(wr_iot_activation_owner_execute(&owner,&input,1,1,0)==WR_IOT_RESULT_REJECTED);
  wr_iot_rc_shutdown.pending=0;
  unsigned initial_queries=idle_reads;
  for(unsigned fault=1;fault<=7;fault++){
   struct wr_iot_control_request failed=input;
   snprintf(failed.id,sizeof(failed.id),"%032x",16+fault);failed.created=3+fault;
   assert(wr_iot_request_read(&failed.request,candidate_read,NULL,1,1,0,NULL,0));
   network_fault=fault;
   assert(wr_iot_activation_owner_execute(&owner,&failed,1,1,0)==WR_IOT_RESULT_RECOVERY);
   if(fault==5){writes=0;fail_write=8;}
   enum wr_iot_result_state rejected=WR_IOT_RESULT_RECOVERY;
   for(unsigned budget=0;budget<50&&rejected==WR_IOT_RESULT_RECOVERY;budget++){
    rejected=wr_iot_activation_owner_continue(&owner,failed.id,failed.created);
    if(owner.start.phase==WR_IOT_RUN_PRE_ROLLBACK)fail_write=0;
   }
   fail_write=0;
   assert(rejected==WR_IOT_RESULT_REJECTED&&owner.phase==WR_IOT_OWNER_REJECTED);
   assert(!depth&&!bridge_index&&!rollback_dns&&!owner.start.admission.snapshot.active);
   assert(owner.start.prior_closed.valid&&!owner.start.prior_closed.submitted&&idle_reads==initial_queries);
   assert(wr_iot_activation_owner_execute(&owner,&failed,1,1,0)==WR_IOT_RESULT_REJECTED);
  }
  network_fault=0;
  struct wr_iot_control_request post_open=input;post_open.id[0]='4';post_open.created=20;
  assert(wr_iot_request_read(&post_open.request,candidate_read,NULL,1,1,0,NULL,0));
  commit_fault=1;
  assert(wr_iot_activation_owner_execute(&owner,&post_open,1,1,0)==WR_IOT_RESULT_RECOVERY);
  enum wr_iot_result_state recovered=WR_IOT_RESULT_RECOVERY;
  for(unsigned budget=0;budget<65&&recovered==WR_IOT_RESULT_RECOVERY;budget++)
   recovered=wr_iot_activation_owner_continue(&owner,post_open.id,post_open.created);
  assert(recovered==WR_IOT_RESULT_REJECTED&&owner.phase==WR_IOT_OWNER_REJECTED);
  assert(owner.start.prior_closed.submitted&&!depth&&!bridge_index&&!rollback_dns);
  assert(owner.start.rollback.phase==WR_IOT_ROLL_DONE&&closes==2&&releases==2);
  int recovered_guard=wr_iot_service_guard_enter(1);assert(recovered_guard==1);
  struct wr_iot_reopen_witness new_closed={0};
  owner.start.close.close_serial++;
  assert(!wr_iot_reopen_recovered_witness_take(&new_closed,&owner.start)&&!new_closed.valid);
  owner.start.close.close_serial--;
  owner.start.rollback.phase=WR_IOT_ROLL_FINISH;
  assert(!wr_iot_reopen_recovered_witness_take(&new_closed,&owner.start)&&!new_closed.valid);
  owner.start.rollback.phase=WR_IOT_ROLL_DONE;
  assert(wr_iot_reopen_recovered_witness_take(&new_closed,&owner.start));
  wr_iot_service_guard_leave(recovered_guard);assert(!depth);
  commit_fault=0;
  struct wr_iot_control_request second=input;second.id[0]='2';second.created=30;
  assert(wr_iot_request_read(&second.request,candidate_read,NULL,1,1,0,NULL,0));
  struct wr_iot_control_request invalid=second;invalid.request.ssid[0]=0;
  assert(wr_iot_activation_owner_execute(&owner,&invalid,1,1,0)==WR_IOT_RESULT_REJECTED);
  assert(owner.phase==WR_IOT_OWNER_REJECTED&&!owner.stop.active&&!owner.stop.complete);
  assert(owner.start.phase==WR_IOT_RUN_REJECTED);
  assert(wr_iot_activation_owner_execute(&owner,&second,1,1,0)==WR_IOT_RESULT_RECOVERY);
  assert(owner.phase==WR_IOT_OWNER_START&&owner.start.prior_closed.valid);
  assert(owner.start.admission.reopened&&!owner.stop.owner&&!owner.stop.active);
  assert(wr_iot_activation_owner_execute(&owner,&second,1,1,0)==WR_IOT_RESULT_RECOVERY);
  enum wr_iot_result_state second_result=WR_IOT_RESULT_RECOVERY;
  for(unsigned budget=0;budget<40&&second_result==WR_IOT_RESULT_RECOVERY;budget++)
   second_result=wr_iot_activation_owner_continue(&owner,second.id,second.created);
  assert(second_result==WR_IOT_RESULT_APPLIED&&owner.phase==WR_IOT_OWNER_ACTIVE);
  assert(owner.start.prior_closed.submitted);
  struct wr_iot_control_request second_off={.id="03030303030303030303030303030303",.created=31};
  assert(wr_iot_activation_owner_execute(&owner,&second_off,1,1,0)==WR_IOT_RESULT_RECOVERY);
  assert(owner.stop.active==&owner.start&&owner.phase==WR_IOT_OWNER_STOP);
  second_result=WR_IOT_RESULT_RECOVERY;
  for(unsigned budget=0;budget<55&&second_result==WR_IOT_RESULT_RECOVERY;budget++)
   second_result=wr_iot_activation_owner_continue(&owner,second_off.id,second_off.created);
  assert(second_result==WR_IOT_RESULT_APPLIED&&owner.phase==WR_IOT_OWNER_OFF&&!depth);
  assert(owner.stop.active==&owner.start&&owner.start.phase==WR_IOT_RUN_STOPPED);
  assert(closes==3&&progresses==3&&releases==3&&!bridge_index&&!rollback_dns);


#undef s

 }
 puts("PASS owner reopen recovery:7 pre-OPEN faults, post-OPEN rollback/new CLOSED witness with stale/incomplete refusal, successful retry and normal OFF; driver/commit/network hooks injected");
}
'''
with tempfile.TemporaryDirectory(prefix='iot-activation-owner-compose-') as d:
 subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
 unit=Path(d)/'check.c';unit.write_text(prefix+body);binary=Path(d)/'check'
 units=('reopen-admission.c','reopen-start.c','reopen-network.c','reopen-rollback.c','initial-off.c','activation-owner.c','active-stop.c','start-runner.c','start-network-rollback.c','start-close.c','start-closed-rollback.c','precreated-stop.c','start-admission.c','request-stage.c','request-snapshot.c','disable-services.c','disable-controller.c','profile.c')
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,'-I'+str(here),str(unit),*[str(here/n) for n in units],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
