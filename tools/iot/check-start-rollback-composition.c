#define WR_IOT_START_FIXTURE_NO_MAIN 1
#include "check-start-staging-composition.c"
#include "start-network-rollback.h"
static int rollback_dns,abort_calls;
int wr_iot_bridge_set_up(int up){assert(!up&&depth);return 1;}
int wr_iot_bridge_detach(void){assert(depth);return 1;}
int wr_iot_bridge_remove(void){assert(depth);bridge_index=0;return 1;}
int wr_iot_dns_activation_recovery_state(void){assert(depth);return rollback_dns;}
int wr_iot_dns_activation_abort(void){assert(depth&&!bridge_index&&rollback_dns==1);abort_calls++;rollback_dns=0;return 1;}
int main(void){
 unsigned char nonce[16]={1};
 for(int failure=0;failure<=18;failure++){
  struct wr_iot_start_admission owner={0};struct wr_iot_start_network network={.phase=WR_IOT_NET_RECOVERY,.attempted=127};
  struct wr_iot_start_network_rollback rollback={0};struct wr_iot_open_controller open={0};
  reset();idle_reads=0;abort_calls=0;rollback_dns=1;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_start_admission_begin(&owner,nonce));
  char baseline[9][128];for(unsigned i=0;i<9;i++)strcpy(baseline[i],values[7+i].value);
  assert(wr_iot_start_admission_stage(&owner,nonce,candidate_read,NULL,1,1,0));
  bridge_index=7;wr_iot_rc_shutdown.pending=SIGTERM;
  while(rollback.phase<WR_IOT_ROLL_SETTINGS)assert(!wr_iot_start_network_rollback_step(&rollback,&network,&owner,&open,nonce));
  assert(!bridge_index&&!rollback_dns&&abort_calls==1&&depth==1);
  writes=0;fail_write=failure;
  int result=wr_iot_start_network_rollback_step(&rollback,&network,&owner,&open,nonce);assert(!result);
  if(failure>0&&failure<=12){assert(rollback.phase==WR_IOT_ROLL_SETTINGS&&owner.snapshot.active&&depth==1);}
  fail_write=0;
  if(rollback.phase==WR_IOT_ROLL_SETTINGS)assert(!wr_iot_start_network_rollback_step(&rollback,&network,&owner,&open,nonce));
  assert(rollback.phase==WR_IOT_ROLL_OBSERVE);
  for(unsigned field=7;field<16;field++){
   char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"newer-writer");int before=writes;
   assert(!wr_iot_start_network_rollback_step(&rollback,&network,&owner,&open,nonce)&&rollback.phase==WR_IOT_ROLL_OBSERVE&&depth==1&&writes==before);
   strcpy(values[field].value,saved);
  }
  assert(!wr_iot_start_network_rollback_step(&rollback,&network,&owner,&open,nonce));
  assert(wr_iot_start_network_rollback_step(&rollback,&network,&owner,&open,nonce)&&!depth);
  for(unsigned i=0;i<9;i++)assert(!strcmp(values[7+i].value,baseline[i]));
  assert(wr_iot_rc_shutdown.pending==SIGTERM);
 }
 puts("PASS actual admission/stage/snapshot/pre-OPEN rollback: partial restore retries and all9 foreign baseline changes retain guard; exact baseline restored, DNS/bridge hooks injected");return 0;
}
