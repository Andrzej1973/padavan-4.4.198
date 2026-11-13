#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include "start-runner.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fault,opens,pre_rolls,closes,post_rolls,commits,normal_off;
int wr_iot_start_admission_begin(struct wr_iot_start_admission *s,const unsigned char *n){assert(n[0]==0x11);s->admitted=s->snapshot.active=s->snapshot.token=1;s->snapshot.owner=getpid();s->idle=(struct wr_iot_idle_result){1,2,1};return 1;}
int wr_iot_start_admission_stage(struct wr_iot_start_admission *s,const unsigned char*n,const char*(*read)(void*,const char*),void*c,int router,int radio,int mode){assert(n&&read&&router==1&&radio==1&&!mode);assert(!strcmp(read(c,"wr_iot_ssid"),"IoT"));if(fault==1)return 0;s->mutation_started=1;if(fault==2)return 0;s->staged=1;return 1;}
int wr_iot_start_admission_cancel(struct wr_iot_start_admission*s){s->snapshot.active=0;return 1;}
int wr_iot_start_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*s,const struct wr_iot_request*r,const unsigned char*nonce){assert(s->staged&&r->enabled&&nonce);n->phase=fault==3?WR_IOT_NET_RECOVERY:WR_IOT_NET_READY;return fault!=3;}
int wr_iot_open_controller_submit(struct wr_iot_open_controller*s,const char*id,const struct wr_iot_request*r){assert(id&&r);opens++;s->owner=getpid();s->attempt=(struct wr_iot_driver_attempt){{1,2},{1}};s->phase=fault==4?WR_IOT_OPEN_RECOVERY:WR_IOT_OPEN_CONFIRMED;return fault!=4;}
int wr_iot_start_close_step(struct wr_iot_start_close*c,const struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o){assert(c&&a&&o);closes++;return 1;}
int wr_iot_start_network_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o,const unsigned char*nonce){assert(b&&n&&o&&nonce);pre_rolls++;a->snapshot.active=0;return 1;}
int wr_iot_start_closed_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o,struct wr_iot_start_close*c){assert(b&&n&&o&&c);post_rolls++;a->snapshot.active=0;return 1;}
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop*s,const struct wr_iot_driver_attempt*a){assert(a);normal_off++;s->phase=WR_IOT_STOP_CLOSE_BEGIN;return 1;}
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop*s){s->phase=WR_IOT_STOP_COMPLETE;s->close.phase=WR_IOT_CLOSE_OWNER_RELEASED;s->close_serial=5;return 1;}
#include <fcntl.h>
static int dns=1;
int wr_iot_service_guard_dup(void){return open("/dev/null",O_RDONLY);}
int wr_iot_request_stage_matches(const struct wr_iot_request*r){assert(r->enabled);return fault!=5;}
int wr_iot_network_services_ready(const char*g){assert(g);return 1;}
int wr_iot_active_filter_observed_current(void){return 1;}
int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt*a,struct wr_iot_driver_open_current_result*r){assert(a->request_id[0]==1);*r=(struct wr_iot_driver_open_current_result){1,2,3};return 1;}
int wr_iot_dns_activation_recovery_state(void){return dns;}
int wr_iot_dns_activation_commit(void){commits++;if(fault==6)return 0;dns=0;return 1;}
int wr_iot_request_snapshot_suspend(struct wr_iot_request_snapshot*s){if(fault==7)return 0;s->token=0;s->expected_valid=1;return 1;}
#include "start-commit.c"

int wr_iot_reopen_start_begin(struct wr_iot_start_admission *a,const struct wr_iot_reopen_witness *w){(void)a;(void)w;assert(0);return 0;}
int wr_iot_reopen_start_stage(struct wr_iot_start_admission*a,const struct wr_iot_reopen_witness*w,const char*(*r)(void*,const char*),void*c,int x,int y,int z){(void)a;(void)w;(void)r;(void)c;(void)x;(void)y;(void)z;assert(0);return 0;}
int wr_iot_reopen_network_step(struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_request*r,const struct wr_iot_reopen_witness*w){(void)n;(void)a;(void)r;(void)w;assert(0);return 0;}
int wr_iot_reopen_rollback_step(struct wr_iot_start_network_rollback*b,struct wr_iot_start_network*n,struct wr_iot_start_admission*a,const struct wr_iot_open_controller*o,const struct wr_iot_reopen_witness*w){(void)b;(void)n;(void)a;(void)o;(void)w;assert(0);return 0;}
int wr_iot_reopen_witness_current(const struct wr_iot_reopen_witness*w){(void)w;assert(0);return 0;}
#include "start-runner.c"
int main(void){
 struct wr_iot_control_request input={.id="11111111111111111111111111111111",.created=1,.request={.enabled=1,.ssid="IoT",.password="password123",.gateway="192.168.50.1",.mask="255.255.255.0",.first="192.168.50.20",.last="192.168.50.200"}};
 for(fault=0;fault<=7;fault++){
  struct wr_iot_start_runner s={0};wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;opens=pre_rolls=closes=post_rolls=commits=normal_off=0;dns=1;
  assert(wr_iot_start_runner_begin(&s,&input,1,1,0));
  assert(!wr_iot_start_runner_begin(&s,&input,1,1,0));
  enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
  for(unsigned i=0;i<10&&result==WR_IOT_RESULT_RECOVERY;i++)result=wr_iot_start_runner_step(&s);
  if(!fault)assert(result==WR_IOT_RESULT_APPLIED&&opens==1&&commits==1&&!pre_rolls&&!closes);
  if(fault==1)assert(result==WR_IOT_RESULT_REJECTED&&!opens&&!pre_rolls&&!closes);
  if(fault==2||fault==3)assert(result==WR_IOT_RESULT_REJECTED&&pre_rolls==1&&!opens&&!closes);
  if(fault==4||fault==5)assert(result==WR_IOT_RESULT_REJECTED&&opens==1&&closes==1&&post_rolls==1&&!pre_rolls);
  if(fault==6)assert(result==WR_IOT_RESULT_RECOVERY&&s.phase==WR_IOT_RUN_UNCERTAIN&&commits==1&&!closes&&!pre_rolls&&s.admission.snapshot.active);
  if(fault==7)assert(result==WR_IOT_RESULT_REJECTED&&normal_off==1&&post_rolls==1&&!pre_rolls&&!closes&&commits==1);
  int count=opens+pre_rolls+closes+post_rolls+commits;
  (void)wr_iot_start_runner_step(&s);assert(count==opens+pre_rolls+closes+post_rolls+commits);
 }
 puts("PASS actual startup runner plus actual two-step commit: success, read-only cancel, pre-OPEN rollback, post-OPEN CLOSE rollback, uncertain DNS commit no replay and confirmed-commit failure routes through normal OFF; component adapters injected");
}
