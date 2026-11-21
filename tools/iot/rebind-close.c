#include <string.h>
#include <unistd.h>
#include "rebind-close.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
int wr_iot_rebind_close_step(struct wr_iot_start_close *s,
 const struct wr_iot_rebind_start *rebind,const struct wr_iot_rebind_open_controller *open)
{
 struct wr_iot_driver_open_recovery_result recovery;
 struct wr_iot_driver_open_current_result receipt;
 struct wr_iot_driver_closed_result closed;
 const struct wr_iot_start_admission *owner;
 unsigned int i,nonzero=0;int fd;
 if(!rebind||rebind->owner!=getpid())return 0;
 if(rebind->physical.action!=WR_STOP_RELEASE||
    !wr_iot_physical_stop_request_valid(&rebind->physical)||
    rebind->identity.device_generation!=rebind->physical.generation)return 0;
 owner=&rebind->admission;
 if(!s||!owner||!open||!wr_iot_rc_shutdown.active||
    owner->reopened!=2||!owner->admitted||!owner->mutation_started||!owner->staged||
    !owner->snapshot.active||owner->snapshot.owner!=getpid()||
    owner->snapshot.token!=1||owner->snapshot.disabling||
    (owner->snapshot.recovering&&s->close.phase!=WR_IOT_CLOSE_OWNER_RELEASED)||
    open->owner!=getpid()||open->busy||
    (open->phase!=WR_REBIND_OPEN_RETAINED&&open->phase!=WR_REBIND_OPEN_CURRENT)||
    !open->attempt.identity.adapter_epoch||!open->attempt.identity.device_generation||
    open->attempt.identity.adapter_epoch!=rebind->identity.adapter_epoch||
    open->attempt.identity.device_generation!=rebind->identity.device_generation||
    open->attempt.identity.adapter_epoch<=rebind->physical.epoch||
    memcmp(open->attempt.request_id,rebind->open_id,sizeof(rebind->open_id)))return 0;
 for(i=0;i<sizeof(open->attempt.request_id);i++)nonzero|=open->attempt.request_id[i];
 if(!nonzero)return 0;
 fd=wr_iot_service_guard_dup();if(fd<0)return 0;if(close(fd))return 0;
 if(s->owner){
  if(s->owner!=getpid()||
     s->attempt.identity.adapter_epoch!=open->attempt.identity.adapter_epoch||
     s->attempt.identity.device_generation!=open->attempt.identity.device_generation||
     memcmp(s->attempt.request_id,open->attempt.request_id,sizeof(s->attempt.request_id)))return 0;
 }else{
  if(s->close.phase!=WR_IOT_CLOSE_IDLE||s->close_serial)return 0;
  s->owner=getpid();s->attempt=open->attempt;
 }
 if(s->close.phase==WR_IOT_CLOSE_IDLE){
  if(!wr_iot_rebind_open_recovery(open,&recovery))return 0;
  receipt.adapter_epoch=recovery.adapter_epoch;
  receipt.device_generation=recovery.device_generation;
  receipt.open_token=recovery.open_token;
  (void)wr_iot_close_controller_begin(&s->close,&s->attempt,&receipt);
  return 0;
 }
 if(s->close.phase!=WR_IOT_CLOSE_OWNER_RELEASED){
  (void)wr_iot_close_controller_advance(&s->close);return 0;
 }
 if(!wr_iot_driver_attempt_closed(&s->attempt,&closed)||
    closed.open_token!=s->close.request.open_token||!closed.close_serial||
    (s->close_serial&&s->close_serial!=closed.close_serial))return 0;
 s->close_serial=closed.close_serial;return 1;
}
