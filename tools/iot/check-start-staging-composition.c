/* Reuse external NVRAM/netdev/guard fixture; link actual admission/stage/snapshot. */
#define main existing_snapshot_checks
#include "check-request-snapshot.c"
#undef main
#include "start-admission.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static unsigned idle_reads;
int wr_iot_driver_initial_idle_read(const unsigned char *nonce,struct wr_iot_idle_result *out){
 assert(depth&&nonce&&nonce[0]==1);
 *out=(struct wr_iot_idle_result){1,2,++idle_reads};return 1;
}
static const char *candidate_read(void *context,const char *key){
 (void)context;
 static const char *const logical[]={"wr_iot_enable","wr_iot_ssid","wr_iot_psk","wr_iot_gateway","wr_iot_mask","wr_iot_start","wr_iot_end"};
 for(unsigned i=0;i<7;i++)if(!strcmp(key,logical[i]))return values[i].value;
 assert(0);return NULL;
}
int main(void){
 assert(existing_snapshot_checks()==0);
 unsigned char nonce[16]={1};
 for(int failure=0;failure<=16;failure++){
  struct wr_iot_start_admission owner={0};reset();idle_reads=0;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  assert(wr_iot_start_admission_begin(&owner,nonce)&&depth==1&&!writes);
  char baseline[9][128];for(unsigned i=0;i<9;i++)strcpy(baseline[i],values[7+i].value);
  fail_write=failure;
  int staged=wr_iot_start_admission_stage(&owner,nonce,candidate_read,NULL,1,1,0);
  assert(staged==(failure==0));
  assert(owner.mutation_started&&owner.snapshot.active&&depth==1);
  int old_writes=writes;
  assert(!wr_iot_start_admission_cancel(&owner)&&writes==old_writes&&depth==1);
  assert(!wr_iot_start_admission_stage(&owner,nonce,candidate_read,NULL,1,1,0)&&writes==old_writes);
  /* This fixture has not created a bridge or attempted OPEN. Exercise the
   * existing restore owner only in that precisely known software boundary. */
  fail_write=0;
  assert(wr_iot_request_snapshot_restore(&owner.snapshot));
  for(unsigned i=0;i<9;i++)assert(!strcmp(values[7+i].value,baseline[i]));
  assert(wr_iot_request_snapshot_finish(&owner.snapshot)&&!depth);
 }
 puts("PASS actual startup admission + staging + snapshot:16 setter faults, retained baseline/guard, cancel/replay refusal and exact restore before bridge/OPEN; external NVRAM/device observations injected");
 return 0;
}
