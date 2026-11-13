#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "start-runner.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fault,opens,pre_rolls,closes,post_rolls,commits,normal_off;
int wr_iot_start_admission_begin(struct wr_iot_start_admission *s,const unsigned char *n){assert(n[0]==0x11);s->admitted=s->snapshot.active=1;return 1;}
int wr_iot_start_admission_stage(struct wr_iot_start_admission *s,const unsigned char*n,const char*(*read)(void*,const char*),void*c,int router,int radio,int mode){assert(n&&read&&router==1&&radio==1&&!mode);assert(!strcmp(read(c,"wr_iot_ssid"),"IoT"));if(fault==1)return 0;s->mutation_started=1;if(fault==2)return 0;s->staged=1;return 1;}
int wr_iot_start_admission_cancel(struct wr_iot_start_admission*s){s->snapshot.active=0;return 1;}
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*s,const struct wr_iot_request*r,const unsigned char*nonce){assert(s->staged&&r->enabled&&nonce);n->phase=fault==3?WR_IOT_NET_RECOVERY:WR_IOT_NET_READY;return fault!=3;}
int wr_iot_open_controller_submit(struct wr_iot_open_controller*s,const char*id,const struct wr_iot_request*r){assert(id&&r);opens++;s->phase=fault==4?WR_IOT_OPEN_RECOVERY:WR_IOT_OPEN_CONFIRMED;return fault!=4;}
int wr_iot_start_commit_step(struct wr_iot_start_commit*s,struct wr_iot_start_admission*a,const struct wr_iot_start_network*n,const struct wr_iot_open_controller*o,const struct wr_iot_request*r){assert(a&&n&&o&&r);commits++;if(fault==5)return 0;if(fault==6){s->phase=WR_IOT_COMMIT_DNS_UNCERTAIN;return 0;}if(s->phase==WR_IOT_COMMIT_IDLE){s->phase=WR_IOT_COMMIT_DNS_COMMITTED;return 0;}if(fault==7)return 0;s->phase=WR_IOT_COMMIT_ACTIVE;return 1;}
int wr_iot_start_close_step(struct wr_iot_start_close*c,const struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o){assert(c&&a&&o);closes++;return 1;}
int wr_iot_start_network_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o,const unsigned char*nonce){assert(b&&n&&o&&nonce);pre_rolls++;a->snapshot.active=0;return 1;}
int wr_iot_start_closed_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o,struct wr_iot_start_close*c){assert(b&&n&&o&&c);post_rolls++;a->snapshot.active=0;return 1;}
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop*s,const struct wr_iot_driver_attempt*a){assert(a);normal_off++;s->phase=WR_IOT_STOP_CLOSE_BEGIN;return 1;}
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop*s){s->phase=WR_IOT_STOP_COMPLETE;s->close.phase=WR_IOT_CLOSE_OWNER_RELEASED;s->close_serial=5;return 1;}
#include "start-runner.c"
int main(void){
 struct wr_iot_control_request input={.id="11111111111111111111111111111111",.created=1,.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 for(fault=0;fault<=7;fault++){
  struct wr_iot_start_runner s={0};wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;opens=pre_rolls=closes=post_rolls=commits=normal_off=0;
  assert(wr_iot_start_runner_begin(&s,&input,1,1,0));
  assert(!wr_iot_start_runner_begin(&s,&input,1,1,0));
  struct wr_iot_start_runner before=s;
  char foreign[33];memcpy(foreign,input.id,33);foreign[0]='2';
  assert(wr_iot_start_runner_continue(&s,foreign,input.created)==WR_IOT_RESULT_RECOVERY);
  assert(wr_iot_start_runner_continue(&s,input.id,input.created+1)==WR_IOT_RESULT_RECOVERY);
  assert(!memcmp(&before,&s,sizeof(s)));
  s.busy=1;before=s;
  assert(wr_iot_start_runner_continue(&s,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  assert(wr_iot_start_runner_step(&s)==WR_IOT_RESULT_RECOVERY);
  assert(!memcmp(&before,&s,sizeof(s)));s.busy=0;
  s.owner=0;before=s;
  assert(wr_iot_start_runner_continue(&s,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  assert(!memcmp(&before,&s,sizeof(s)));s.owner=getpid();
  wr_iot_rc_shutdown.active=0;before=s;
  assert(wr_iot_start_runner_continue(&s,input.id,input.created)==WR_IOT_RESULT_RECOVERY);
  assert(!memcmp(&before,&s,sizeof(s)));wr_iot_rc_shutdown.active=1;
  enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
  for(unsigned i=0;i<10&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_start_runner_continue(&s,input.id,input.created);
  if(!fault)assert(result==WR_IOT_RESULT_APPLIED&&opens==1&&commits==2&&!pre_rolls&&!closes);
  if(fault==1)assert(result==WR_IOT_RESULT_REJECTED&&!opens&&!pre_rolls&&!closes);
  if(fault==2||fault==3)assert(result==WR_IOT_RESULT_REJECTED&&pre_rolls==1&&!opens&&!closes);
  if(fault==4||fault==5)assert(result==WR_IOT_RESULT_REJECTED&&opens==1&&closes==1&&post_rolls==1&&!pre_rolls);
  if(fault==6)assert(result==WR_IOT_RESULT_RECOVERY&&s.phase==WR_IOT_RUN_UNCERTAIN&&commits==1&&!closes&&!pre_rolls&&s.admission.snapshot.active);
  if(fault==7)assert(result==WR_IOT_RESULT_REJECTED&&normal_off==1&&post_rolls==1&&!pre_rolls&&!closes&&commits==2);
  int count=opens+pre_rolls+closes+post_rolls+commits;
  (void)wr_iot_start_runner_step(&s);assert(count==opens+pre_rolls+closes+post_rolls+commits);
 }
 puts("PASS actual startup runner: success, read-only cancel, pre-OPEN rollback, post-OPEN CLOSE rollback, uncertain DNS commit no replay and confirmed-commit failure routes through normal OFF; component adapters injected");
}
