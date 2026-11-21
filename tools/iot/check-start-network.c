#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <fcntl.h>
#include <unistd.h>
#include "start-network.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int fail,operations,bridge,quarantine,attached,up,network,dns,policy;
static unsigned serial;
int wr_iot_service_guard_dup(void){return open("/dev/null",O_RDONLY);}
int wr_iot_driver_initial_idle_read(const unsigned char *n,struct wr_iot_idle_result *out){assert(n[0]==1);*out=(struct wr_iot_idle_result){1,2,++serial};return 1;}
int wr_iot_bss_is_down(void){return 1;}
static int next(int phase){operations++;return fail!=phase;}
int wr_iot_network_check(const char*a,const char*b,const char*c,const char*d){assert(a&&b&&c&&d);return 1;}
int wr_iot_bridge_prepare(const char*a,const char*b,const char*c,const char*d,const struct wr_iot_range*r,size_t n){assert(a&&b&&c&&d&&!r&&!n);if(!next(1))return 0;bridge=1;return 1;}
int wr_iot_quarantine_apply(void){assert(bridge&&!up);if(!next(2))return 0;quarantine=1;return 1;}
int wr_iot_bridge_attach(void){assert(bridge&&quarantine);if(!next(3))return 0;attached=1;return 1;}
int wr_iot_bridge_set_up(int enabled){assert(enabled&&attached&&quarantine);if(!next(4))return 0;up=1;return 1;}
int wr_iot_request_network_enable(const struct wr_iot_request*r){assert(r&&up&&quarantine&&!policy);if(!next(5))return 0;network=1;return 1;}
int wr_iot_dns_activation_prepare(void){assert(up&&network&&!policy);if(!next(6))return 1;dns=1;return 0;}
int wr_iot_policy_enable_current(void){assert(dns&&network);if(!next(7))return 0;policy=1;return 1;}
int wr_iot_request_prepared_matches(const struct wr_iot_request*r,int n,int f){assert(r);return n==network&&f==policy;}
int wr_iot_request_stage_matches(const struct wr_iot_request*r){assert(r&&policy);return 1;}
int wr_iot_network_services_ready(const char*g){assert(g&&dns);return 1;}
int wr_iot_active_filter_ready_current(void){return policy;}
#include "start-network.c"
int main(void){
 for(fail=0;fail<=8;fail++){
  struct wr_iot_start_network state={0};struct wr_iot_start_admission owner={0};
  owner.admitted=owner.mutation_started=owner.staged=owner.snapshot.active=1;owner.snapshot.owner=getpid();owner.snapshot.token=1;owner.idle=(struct wr_iot_idle_result){1,2,1};
  struct wr_iot_request request={.enabled=1};unsigned char nonce[16]={1};
  serial=1;operations=bridge=quarantine=attached=up=network=dns=policy=0;
  wr_iot_rc_shutdown.active=1;wr_iot_rc_shutdown.pending=0;
  int ready=0;
  for(unsigned budget=0;budget<9&&!ready&&state.phase!=WR_IOT_NET_RECOVERY;budget++){
   if(fail==8&&state.phase==WR_IOT_NET_DNS)wr_iot_rc_shutdown.pending=SIGTERM;
   ready=wr_iot_start_network_step(&state,&owner,&request,nonce);
  }
  assert(ready==(fail==0));assert(owner.snapshot.active&&owner.mutation_started);
  unsigned int expected=fail==0?127U:fail==8?31U:((1U<<(unsigned int)fail)-1U);
  assert(state.attempted==expected);
  if(fail){assert(state.phase==WR_IOT_NET_RECOVERY);int before=operations;assert(!wr_iot_start_network_step(&state,&owner,&request,nonce)&&operations==before);}
  else assert(state.phase==WR_IOT_NET_READY&&operations==7&&policy);
 }
 puts("PASS actual pre-OPEN network sequencer: seven ordered operations, each failure and pending shutdown retain startup snapshot/recovery without replay; external resource adapters injected");return 0;
}
