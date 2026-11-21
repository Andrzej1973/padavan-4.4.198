#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include "driver-open-controller.h"
static int fault,guards,matches,submits,observes,reads,recovery_ok=1;
static enum wr_iot_driver_submit_result outcome;
static struct wr_iot_open_controller *current_owner;
int wr_iot_service_guard_dup(void){guards++;return fault==1||(fault==9&&guards>1)?-1:open("/dev/null",O_RDONLY);}
int wr_iot_request_stage_matches(const struct wr_iot_request *r){assert(r&&r->enabled);matches++;return fault!=2&&!(fault==7&&matches>=2)&&!(fault==10&&matches>=3);}
int wr_iot_bss_is_down(void){return fault!=3;}
int wr_iot_network_check(const char *g,const char *m,const char *a,const char *b){assert(g&&m&&a&&b);return fault!=4;}
int wr_iot_bridge_address_matches(const char *g,const char *m){assert(g&&m);return fault!=5;}
int wr_iot_network_services_ready(const char *g){assert(g);return fault!=6;}
int wr_iot_active_filter_ready_current(void){return fault!=8;}
int wr_iot_active_filter_observed_current(void){observes++;return fault!=11;}
enum wr_iot_driver_submit_result wr_iot_driver_open_requested_tracked(const char *id,const struct wr_iot_request *r,struct wr_iot_driver_attempt *a){
 assert(id&&r&&current_owner->phase==WR_IOT_OPEN_SUBMITTING&&current_owner->owner==getpid());
 assert(!wr_iot_open_controller_submit(current_owner,id,r));submits++;
 memset(a,0,sizeof(*a));if(outcome!=WR_IOT_DRIVER_NOT_SUBMITTED){a->identity.adapter_epoch=1;a->identity.device_generation=2;a->request_id[0]=1;}
 return outcome;
}
int wr_iot_driver_open_recovery_read(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_open_recovery_result *r){assert(a->request_id[0]==1&&a->identity.device_generation==2);reads++;memset(r,0,sizeof(*r));if(!recovery_ok)return 0;*r=(struct wr_iot_driver_open_recovery_result){1,2,3};return 1;}
#include "driver-open-controller.c"
int main(void){
 const char *id="01000000000000000000000000000000";
 struct wr_iot_request request={.enabled=1};
 for(int failure=0;failure<=11;failure++)for(int mode=0;mode<3;mode++){
  struct wr_iot_open_controller s={0};current_owner=&s;
  fault=failure;guards=matches=submits=observes=reads=0;outcome=(enum wr_iot_driver_submit_result)mode;
  int success=wr_iot_open_controller_submit(&s,id,&request);
  int before=failure>=1&&failure<=8;
  assert(success==(!failure&&outcome==WR_IOT_DRIVER_OPEN_COMPLETED));
  assert(submits==!before);
  if(before){assert(s.phase==WR_IOT_OPEN_IDLE&&!s.owner);continue;}
  assert(s.phase==(outcome==WR_IOT_DRIVER_NOT_SUBMITTED?WR_IOT_OPEN_NOT_SUBMITTED:
    success?WR_IOT_OPEN_CONFIRMED:WR_IOT_OPEN_RECOVERY));
  assert(!wr_iot_open_controller_submit(&s,id,&request)&&submits==1);
  struct wr_iot_driver_open_recovery_result receipt={99,99,99};fault=0;
  if(outcome==WR_IOT_DRIVER_NOT_SUBMITTED){assert(!s.attempt.request_id[0]);assert(!wr_iot_open_controller_recovery_read(&s,&receipt)&&!receipt.open_token);continue;}
  struct wr_iot_driver_attempt retained=s.attempt;
  assert(wr_iot_open_controller_recovery_read(&s,&receipt)&&receipt.open_token==3);
  s.owner++;assert(!wr_iot_open_controller_recovery_read(&s,&receipt)&&!receipt.open_token);s.owner--;
  recovery_ok=0;assert(!wr_iot_open_controller_recovery_read(&s,&receipt)&&!receipt.open_token);recovery_ok=1;
  assert(!memcmp(&retained,&s.attempt,sizeof(retained))&&submits==1);
 }
 puts("PASS actual OPEN controller:11 pre/post readiness failures across3 transport outcomes, one submission/reentrancy refusal, retained recovery identity and owner checks; external adapters injected, no RF/runtime acceptance");
 return 0;
}
