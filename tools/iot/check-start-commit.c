#include <assert.h>
#include <stdio.h>
#include <unistd.h>
#include <fcntl.h>
#include "start-commit.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fault,commits,suspends,dns=1;
int wr_iot_service_guard_dup(void){return fault==1?-1:open("/dev/null",O_RDONLY);}
int wr_iot_request_stage_matches(const struct wr_iot_request *r){assert(r->enabled);return fault!=2;}
int wr_iot_network_services_ready(const char *g){assert(g);return fault!=3;}
int wr_iot_active_filter_observed_current(void){return fault!=4;}
int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_open_current_result *r){assert(a->request_id[0]==1);*r=(struct wr_iot_driver_open_current_result){1,2,3};return fault!=5;}
int wr_iot_dns_activation_recovery_state(void){return dns;}
int wr_iot_dns_activation_commit(void){commits++;if(fault==6)return 0;dns=0;return 1;}
int wr_iot_request_snapshot_suspend(struct wr_iot_request_snapshot *s){suspends++;if(fault==7)return 0;s->token=0;s->expected_valid=1;return 1;}
#include "start-commit.c"
int main(void){
 for(int failure=0;failure<=7;failure++){
  struct wr_iot_start_commit state={0};
  struct wr_iot_start_admission owner={.admitted=1,.staged=1,.mutation_started=1,.idle={1,2,1}};
  owner.snapshot.active=owner.snapshot.token=1;owner.snapshot.owner=getpid();
  struct wr_iot_start_network network={.phase=WR_IOT_NET_READY};
  struct wr_iot_open_controller open={.owner=getpid(),.phase=WR_IOT_OPEN_CONFIRMED,.attempt={{1,2},{1}}};
  struct wr_iot_request request={.enabled=1};
  fault=failure;commits=suspends=0;dns=1;wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request));
  if(failure>=1&&failure<=5){assert(!commits&&owner.snapshot.token==1);fault=0;assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request));}
  if(failure==6){
   assert(state.phase==WR_IOT_COMMIT_DNS_UNCERTAIN&&commits==1&&owner.snapshot.token==1);
   fault=0;assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&commits==1&&!suspends);continue;
  }
  assert(state.phase==WR_IOT_COMMIT_DNS_COMMITTED&&commits==1&&owner.snapshot.token==1);
  wr_iot_rc_shutdown.pending=SIGTERM;assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&!suspends);wr_iot_rc_shutdown.pending=0;
  open.attempt.request_id[1]=1;assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&!suspends);open.attempt.request_id[1]=0;
  if(failure==7){assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&owner.snapshot.token==1);fault=0;}
  assert(wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&state.phase==WR_IOT_COMMIT_ACTIVE);
  assert(owner.snapshot.active&&!owner.snapshot.token&&owner.snapshot.expected_valid&&commits==1);
  int count=suspends;assert(!wr_iot_start_commit_step(&state,&owner,&network,&open,&request)&&suspends==count&&commits==1);
 }
 puts("PASS startup final commit:7 readiness/commit/suspend faults, one DNS commit attempt, retained uncertainty, pending shutdown/foreign nonce refusal, retained suspended baseline; resource adapters injected");
}
