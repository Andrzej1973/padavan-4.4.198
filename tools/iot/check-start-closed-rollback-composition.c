#define WR_IOT_START_FIXTURE_NO_MAIN 1
#include "check-start-staging-composition.c"
#include "start-closed-rollback.h"
static int rollback_dns,abort_calls;
int wr_iot_bridge_set_up(int up){assert(!up&&depth);return 1;}
int wr_iot_bridge_detach(void){assert(depth);return 1;}
int wr_iot_bridge_remove(void){assert(depth);bridge_index=0;return 1;}
int wr_iot_dns_activation_recovery_state(void){assert(depth);return rollback_dns;}
int wr_iot_dns_activation_abort(void){assert(depth&&!bridge_index&&rollback_dns==1);abort_calls++;rollback_dns=0;return 1;}
static unsigned long long observed_serial=0x100000001ULL;
int wr_iot_open_controller_recovery_read(const struct wr_iot_open_controller *s,struct wr_iot_driver_open_recovery_result *r){(void)s;(void)r;assert(0);return 0;}
int wr_iot_close_controller_begin(struct wr_iot_close_controller *s,const struct wr_iot_driver_attempt *a,const struct wr_iot_driver_open_current_result *r){(void)s;(void)a;(void)r;assert(0);return 0;}
int wr_iot_close_controller_advance(struct wr_iot_close_controller *s){(void)s;assert(0);return 0;}
int wr_iot_driver_attempt_closed(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_closed_result *r){assert(a->identity.adapter_epoch==1&&a->request_id[0]==1);*r=(struct wr_iot_driver_closed_result){1,2,3,observed_serial};return 1;}
int main(void){
 unsigned char nonce[16]={1};
 for(int failure=0;failure<=18;failure++){
  struct wr_iot_start_admission owner={0};struct wr_iot_start_network network={.phase=WR_IOT_NET_RECOVERY,.attempted=127};
  struct wr_iot_start_network_rollback rollback={0};struct wr_iot_open_controller open={.owner=getpid(),.phase=WR_IOT_OPEN_RECOVERY,.attempt={{1,2},{1}}};
  struct wr_iot_start_close closed={.owner=getpid(),.attempt={{1,2},{1}},.close={.phase=WR_IOT_CLOSE_OWNER_RELEASED,.request={.open_token=3}},.close_serial=0x100000001ULL};
  reset();idle_reads=0;abort_calls=0;rollback_dns=1;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_start_admission_begin(&owner,nonce));
  char baseline[9][128];for(unsigned i=0;i<9;i++)strcpy(baseline[i],values[7+i].value);
  assert(wr_iot_start_admission_stage(&owner,nonce,candidate_read,NULL,1,1,0));
  bridge_index=7;wr_iot_rc_shutdown.pending=SIGTERM;
  while(rollback.phase<WR_IOT_ROLL_SETTINGS)assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed));
  assert(!bridge_index&&!rollback_dns&&abort_calls==1&&depth==1);
  writes=0;fail_write=failure;
  int result=wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed);assert(!result);
  if(failure>0&&failure<=12){assert(rollback.phase==WR_IOT_ROLL_SETTINGS&&owner.snapshot.active&&depth==1);}
  fail_write=0;
  if(rollback.phase==WR_IOT_ROLL_SETTINGS)assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed));
  assert(rollback.phase==WR_IOT_ROLL_OBSERVE);
  for(unsigned field=7;field<16;field++){
   char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"newer-writer");int before=writes;
   assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed)&&rollback.phase==WR_IOT_ROLL_OBSERVE&&depth==1&&writes==before);
   strcpy(values[field].value,saved);
  }
  assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed));
  observed_serial++;int before=writes;
  assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed)&&depth==1&&writes==before);
  observed_serial--;
  for(unsigned field=7;field<16;field++){
   char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"foreign-at-finish");
   assert(!wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed)&&depth==1&&writes==before);
   strcpy(values[field].value,saved);
  }
  assert(wr_iot_start_closed_rollback_step(&rollback,&network,&owner,&open,&closed)&&!depth);
  for(unsigned i=0;i<9;i++)assert(!strcmp(values[7+i].value,baseline[i]));
  assert(wr_iot_rc_shutdown.pending==SIGTERM);
 }
 puts("PASS actual admission/stage/snapshot/post-CLOSE rollback: partial restore retries and all9 foreign baseline changes retain guard; fresh64 CLOSED serial and all9 final baseline values checked before release; DNS/bridge/driver hooks injected");return 0;
}
