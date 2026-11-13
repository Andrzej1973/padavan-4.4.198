#define WR_IOT_START_FIXTURE_NO_MAIN 1
#include "check-start-staging-composition.c"
#include "start-commit.h"
static int dns=1,commits;
int wr_iot_network_services_ready(const char *g){assert(g&&depth);return 1;}
int wr_iot_active_filter_observed_current(void){assert(depth);return 1;}
int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_open_current_result *r){assert(depth&&a->request_id[0]==1);*r=(struct wr_iot_driver_open_current_result){1,2,3};return 1;}
int wr_iot_dns_activation_recovery_state(void){assert(depth);return dns;}
int wr_iot_dns_activation_commit(void){assert(depth==2&&dns==1);commits++;dns=0;wr_iot_service_guard_leave(1);return 1;}
int main(void){
 unsigned char nonce[16]={1};struct wr_iot_start_admission owner={0};
 struct wr_iot_start_commit state={0};struct wr_iot_start_network network={.phase=WR_IOT_NET_READY};
 struct wr_iot_open_controller open={.owner=getpid(),.phase=WR_IOT_OPEN_CONFIRMED,.attempt={{1,2},{1}}};
 struct wr_iot_request request={.enabled=1};
 reset();idle_reads=0;wr_iot_rc_shutdown.active=1;
 assert(wr_iot_start_admission_begin(&owner,nonce));
 char baseline[9][128];for(unsigned i=0;i<9;i++)strcpy(baseline[i],values[7+i].value);
 assert(wr_iot_start_admission_stage(&owner,nonce,candidate_read,NULL,1,1,0));
 strcpy(values[8].value,"1");strcpy(values[9].value,"1");
 strcpy(request.ssid,values[10].value);strcpy(request.password,values[11].value);
 strcpy(request.gateway,values[12].value);strcpy(request.mask,values[13].value);
 strcpy(request.first,values[14].value);strcpy(request.last,values[15].value);
 bridge_index=7;assert(wr_iot_service_guard_enter(1)==1&&depth==2);
 assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&commits==1&&depth==1);
 assert(wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&!depth);
 assert(owner.snapshot.active&&!owner.snapshot.token&&owner.snapshot.expected_valid);
 for(unsigned field=7;field<16;field++){
  char saved[128];strcpy(saved,values[field].value);strcpy(values[field].value,"foreign-active");
  assert(!wr_iot_request_snapshot_resume(&owner.snapshot)&&!depth&&!owner.snapshot.token);
  strcpy(values[field].value,saved);
 }
 assert(wr_iot_request_snapshot_resume(&owner.snapshot)&&depth==1);
 for(unsigned i=0;i<9;i++)assert(!strcmp(owner.snapshot.values[i],baseline[i]));
 /* Fixture only: administrative/radio/bridge teardown is injected here. */
 bridge_index=0;
 assert(wr_iot_request_snapshot_restore(&owner.snapshot));
 assert(wr_iot_request_snapshot_restored_current(&owner.snapshot));
 assert(wr_iot_request_snapshot_finish(&owner.snapshot)&&!depth&&commits==1);
 puts("PASS actual startup admission/staging/final commit/snapshot suspend-resume: nested DNS guard released first, all9 foreign ACTIVE changes refuse resume, original baseline retained and restored; DNS/driver/network adapters injected");
}
