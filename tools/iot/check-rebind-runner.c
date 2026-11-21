#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "rebind-runner.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fault,opens,pre_rolls,closes,post_rolls,commits,normal_off;
int wr_iot_rebind_start_begin(struct wr_iot_rebind_start *s,const struct wr_iot_physical_stop_request *p,const unsigned char *n){
 assert(n[0]==0x11);s->owner=getpid();s->physical=*p;s->identity=(struct wr_iot_driver_identity){2,2};memcpy(s->open_id,n,16);s->admission.admitted=s->admission.snapshot.active=1;s->admission.reopened=2;return 1;
}
int wr_iot_rebind_start_stage(struct wr_iot_rebind_start*s,const char*(*read)(void*,const char*),void*c,int router,int radio,int mode){assert(read&&router==1&&radio==1&&!mode);assert(!strcmp(read(c,"wr_iot_ssid"),"IoT"));if(fault==1)return 0;s->admission.mutation_started=1;if(fault==2)return 0;s->admission.staged=1;return 1;}
int wr_iot_start_admission_cancel(struct wr_iot_start_admission*s){s->snapshot.active=0;return 1;}
int wr_iot_rebind_network_step(struct wr_iot_start_network*n,struct wr_iot_rebind_start*s,const struct wr_iot_request*r){assert(s->admission.staged&&r->enabled);n->phase=fault==3?WR_IOT_NET_RECOVERY:WR_IOT_NET_READY;return fault!=3;}
int wr_iot_rebind_open_submit(struct wr_iot_rebind_open_controller*s,const struct wr_iot_physical_rebind_request*r){
 assert(r->operation==WR_REBIND_OPEN&&r->physical.epoch==1&&r->open.adapter_epoch==2&&r->open.device_generation==2&&r->open.request_id[0]==0x11);
 assert(r->open.ssid_length==3&&!memcmp(r->open.ssid,"IoT",3));assert(r->open.password_length==11&&!memcmp(r->open.password,"password123",11));
 opens++;s->owner=getpid();s->attempt.identity=(struct wr_iot_driver_identity){2,2};memcpy(s->attempt.request_id,r->open.request_id,16);s->phase=WR_REBIND_OPEN_RETAINED;
 if(fault==11){memset(&s->attempt,0,sizeof(s->attempt));s->phase=WR_REBIND_OPEN_NOT_SUBMITTED;return 0;}return fault!=4;
}
int wr_iot_rebind_open_current(struct wr_iot_rebind_open_controller*s,struct wr_iot_driver_open_current_result*r){assert(s->phase==WR_REBIND_OPEN_RETAINED);if(fault==12)return 0;s->phase=WR_REBIND_OPEN_CURRENT;*r=(struct wr_iot_driver_open_current_result){2,2,3};return 1;}
int wr_iot_rebind_configuration_current(const struct wr_iot_physical_stop_request*p,const unsigned char*n,struct wr_iot_driver_identity*r){assert(p->epoch==1&&n[0]==0x11);*r=(struct wr_iot_driver_identity){fault==9?3:2,2};return 1;}
int wr_iot_request_stage_matches(const struct wr_iot_request*r){assert(r->enabled);return fault!=8;}
int wr_iot_bss_is_down(void){return 1;}
int wr_iot_network_check(const char*a,const char*b,const char*c,const char*d){assert(a&&b&&c&&d);return 1;}
int wr_iot_bridge_address_matches(const char*a,const char*b){assert(a&&b);return 1;}
int wr_iot_network_services_ready(const char*a){assert(a);return 1;}
int wr_iot_active_filter_ready_current(void){return 1;}
int wr_iot_active_filter_observed_current(void){return fault!=10;}
int wr_iot_rebind_commit_step(struct wr_iot_start_commit*s,struct wr_iot_rebind_start*a,const struct wr_iot_start_network*n,const struct wr_iot_rebind_open_controller*o,const struct wr_iot_request*r){assert(a&&n&&o&&r);commits++;if(fault==5)return 0;if(fault==6){s->phase=WR_IOT_COMMIT_DNS_UNCERTAIN;return 0;}if(s->phase==WR_IOT_COMMIT_IDLE){s->phase=WR_IOT_COMMIT_DNS_COMMITTED;return 0;}if(fault==7)return 0;s->phase=WR_IOT_COMMIT_ACTIVE;return 1;}
int wr_iot_rebind_close_step(struct wr_iot_start_close*c,const struct wr_iot_rebind_start*a,const struct wr_iot_rebind_open_controller*o){assert(c&&a&&o);closes++;return 1;}
int wr_iot_rebind_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_rebind_start*a,const struct wr_iot_rebind_open_controller*o){assert(b&&n&&o);pre_rolls++;a->admission.snapshot.active=0;return 1;}
int wr_iot_rebind_closed_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_rebind_start*a,const struct wr_iot_rebind_open_controller*o,struct wr_iot_start_close*c){assert(b&&n&&o&&c);post_rolls++;a->admission.snapshot.active=0;return 1;}
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop*s,const struct wr_iot_driver_attempt*a){assert(a);normal_off++;s->phase=WR_IOT_STOP_CLOSE_BEGIN;return 1;}
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop*s){s->phase=WR_IOT_STOP_COMPLETE;s->close.phase=WR_IOT_CLOSE_OWNER_RELEASED;s->close_serial=5;return 1;}
#include "rebind-runner.c"
int main(void){
 struct wr_iot_control_request input={.id="11111111111111111111111111111111",.created=1,.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 struct wr_iot_physical_stop_request p={.action=WR_STOP_RELEASE,.epoch=1,.generation=2,.open_token=3,.closed_serial=4,.attempt=5,.nonce={1}};
 for(fault=0;fault<=13;fault++){
  struct wr_iot_rebind_runner s={0};wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;opens=pre_rolls=closes=post_rolls=commits=normal_off=0;
  assert(wr_iot_rebind_runner_begin(&s,&input,&p,1,1,0));
  assert(!wr_iot_rebind_runner_begin(&s,&input,&p,1,1,0));
  struct wr_iot_rebind_runner before=s;
  char foreign[33];memcpy(foreign,input.id,33);foreign[0]='2';
  assert(wr_iot_rebind_runner_continue(&s,foreign,input.created)==WR_IOT_RESULT_RECOVERY);
  assert(wr_iot_rebind_runner_continue(&s,input.id,input.created+1)==WR_IOT_RESULT_RECOVERY);
  assert(!memcmp(&before,&s,sizeof(s)));
  s.busy=1;before=s;assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY);assert(!memcmp(&before,&s,sizeof(s)));s.busy=0;
  s.owner=0;before=s;assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY);assert(!memcmp(&before,&s,sizeof(s)));s.owner=getpid();
  wr_iot_rc_shutdown.active=0;before=s;assert(wr_iot_rebind_runner_step(&s)==WR_IOT_RESULT_RECOVERY);assert(!memcmp(&before,&s,sizeof(s)));wr_iot_rc_shutdown.active=1;
  enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
  for(unsigned i=0;i<14&&result==WR_IOT_RESULT_RECOVERY;i++){
   if(fault==13&&s.phase==WR_IOT_RUN_OPEN)wr_iot_rc_shutdown.pending=SIGTERM;
   result=wr_iot_rebind_runner_continue(&s,input.id,input.created);
  }
  if(!fault)assert(result==WR_IOT_RESULT_APPLIED&&opens==1&&commits==2&&!pre_rolls&&!closes);
  if(fault==1)assert(result==WR_IOT_RESULT_REJECTED&&!opens&&!pre_rolls&&!closes);
  if(fault==2||fault==3||fault==8||fault==9||fault==13)assert(result==WR_IOT_RESULT_REJECTED&&pre_rolls==1&&!opens&&!closes);
  if(fault==4||fault==5||fault==10||fault==12)assert(result==WR_IOT_RESULT_REJECTED&&opens==1&&closes==1&&post_rolls==1&&!pre_rolls);
  if(fault==6)assert(result==WR_IOT_RESULT_RECOVERY&&s.phase==WR_IOT_RUN_UNCERTAIN&&commits==1&&!closes&&!pre_rolls&&s.start.admission.snapshot.active);
  if(fault==7)assert(result==WR_IOT_RESULT_REJECTED&&normal_off==1&&post_rolls==1&&!pre_rolls&&!closes&&commits==2);
  if(fault==11)assert(result==WR_IOT_RESULT_REJECTED&&opens==1&&pre_rolls==1&&!closes);
  int count=opens+pre_rolls+closes+post_rolls+commits+normal_off;
  (void)wr_iot_rebind_runner_step(&s);assert(count==opens+pre_rolls+closes+post_rolls+commits+normal_off);
 }
 puts("PASS retained rebind runner: success and13 faults; exact new epoch/OPEN payload, no replay, immutable continuation identity, pre/post OPEN rollback, pending signal, DNS uncertainty and committed normal OFF; component adapters injected");
}
