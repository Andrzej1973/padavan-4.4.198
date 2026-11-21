#define _GNU_SOURCE
#include <assert.h>
#include <string.h>
#include <unistd.h>
#include "physical-rebind-controller.h"
#include "rc-shutdown-admission.h"
struct wr_iot_rc_shutdown_admission wr_iot_rc_shutdown;
static int guard_ok=1,calls,read_ok=1,drift,identity_calls,identity_drift;
static enum wr_iot_rebind_call_result answer;
int wr_iot_service_guard_dup(void){return guard_ok?42:-1;}
static int mock_close(int fd){assert(fd==42);return 0;}
#define close mock_close
#include "physical-rebind-controller.c"
#undef close
enum wr_iot_rebind_call_result wr_iot_physical_rebind_call(const struct wr_iot_physical_rebind_request *r)
{assert(r->operation==WR_REBIND_OPEN||r->operation==WR_REBIND_OBSERVE);calls++;return answer;}
int wr_iot_driver_open_current_read(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_open_current_result *out)
{assert(a->identity.adapter_epoch==7&&a->identity.device_generation==2&&a->request_id[0]==8);*out=(struct wr_iot_driver_open_current_result){7+(unsigned)drift,2,9};return read_ok;}
int wr_iot_driver_open_recovery_read(const struct wr_iot_driver_attempt *a,struct wr_iot_driver_open_recovery_result *out)
{assert(a->request_id[0]==8);*out=(struct wr_iot_driver_open_recovery_result){7,2,9};return 1;}
int wr_iot_driver_identity_read(struct wr_iot_driver_identity *out,const unsigned char *id)
{assert(id[0]==8);identity_calls++;*out=(struct wr_iot_driver_identity){7+(unsigned)(identity_drift&&identity_calls==2),2};return 1;}
int main(void)
{
 struct wr_iot_physical_rebind_request request={.operation=WR_REBIND_OPEN};
 unsigned mode;
 request.open.adapter_epoch=7;request.open.device_generation=2;request.open.request_id[0]=8;
 for(mode=0;mode<3;mode++){
  struct wr_iot_rebind_open_controller s={0};
  struct wr_iot_driver_open_current_result current;
  struct wr_iot_driver_open_recovery_result recovery;
  answer=(enum wr_iot_rebind_call_result)mode;calls=0;wr_iot_rc_shutdown.active=0;
  assert(!wr_iot_rebind_open_submit(&s,&request)&&!calls&&!s.owner);
  wr_iot_rc_shutdown.active=1;guard_ok=0;
  assert(!wr_iot_rebind_open_submit(&s,&request)&&!calls&&!s.owner);guard_ok=1;
  assert(wr_iot_rebind_open_submit(&s,&request)==(mode==WR_REBIND_IOCTL_RETURNED));
  assert(calls==1&&!wr_iot_rebind_open_submit(&s,&request)&&calls==1);
  if(mode==WR_REBIND_NOT_SUBMITTED){assert(!s.attempt.identity.adapter_epoch&&!wr_iot_rebind_open_current(&s,&current));continue;}
  assert(s.phase==WR_REBIND_OPEN_RETAINED);
  assert(wr_iot_rebind_open_recovery(&s,&recovery)&&s.phase==WR_REBIND_OPEN_RETAINED);
  drift=1;assert(!wr_iot_rebind_open_current(&s,&current)&&!current.open_token);drift=0;
  read_ok=0;assert(!wr_iot_rebind_open_current(&s,&current)&&!current.open_token);read_ok=1;
  s.owner++;assert(!wr_iot_rebind_open_current(&s,&current));s.owner--;
  assert(wr_iot_rebind_open_current(&s,&current)&&s.phase==WR_REBIND_OPEN_CURRENT&&calls==1);
  assert(!wr_iot_rebind_open_submit(&s,&request)&&calls==1);
 }
 {
  struct wr_iot_driver_identity identity;
  unsigned char id[16]={8};
  struct wr_iot_physical_stop_request p={.action=WR_STOP_RELEASE,.epoch=5,.generation=2,.open_token=3,.closed_serial=4,.attempt=6,.nonce={1}};
  wr_iot_rc_shutdown.active=1;answer=WR_REBIND_IOCTL_RETURNED;identity_calls=0;calls=0;
  assert(wr_iot_rebind_configuration_current(&p,id,&identity)&&identity.adapter_epoch==7&&calls==1&&identity_calls==2);
  identity_calls=0;identity_drift=1;
  assert(!wr_iot_rebind_configuration_current(&p,id,&identity)&&!identity.adapter_epoch);identity_drift=0;
  identity_calls=0;answer=WR_REBIND_UNCERTAIN;
  assert(!wr_iot_rebind_configuration_current(&p,id,&identity)&&!identity.adapter_epoch&&identity_calls==1);
  p.epoch=7;identity_calls=0;calls=0;
  assert(!wr_iot_rebind_configuration_current(&p,id,&identity)&&!calls);
 }
 return 0;
}
