#include <string.h>
#include <unistd.h>
#include <net/if.h>
#include "precreated-stop.h"
#include "service-guard.h"
#include "bridge.h"
static int stop_owned(const struct wr_iot_precreated_stop *s)
{
 int fd;
 if(!s||s->guard!=1||s->owner!=getpid())return 0;
 fd=wr_iot_service_guard_dup();
 return fd>=0&&close(fd)==0;
}
int wr_iot_precreated_stop_begin(struct wr_iot_precreated_stop *s,
 const struct wr_iot_driver_attempt *attempt)
{
 unsigned int i,nonzero=0;int guard;
 if(!s||!attempt||s->phase!=WR_IOT_STOP_IDLE||s->guard||s->owner||
    !attempt->identity.adapter_epoch||!attempt->identity.device_generation)return 0;
 for(i=0;i<sizeof(attempt->request_id);i++)nonzero|=attempt->request_id[i];
 if(!nonzero)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_disable_begin_precreated(&s->disable)){
  wr_iot_service_guard_leave(guard);return 0;
 }
 s->attempt=*attempt;s->owner=getpid();s->guard=guard;
 s->phase=WR_IOT_STOP_CLOSE_BEGIN;return 1;
}
int wr_iot_precreated_stop_cancel(struct wr_iot_precreated_stop *s)
{
 if(!stop_owned(s)||s->phase!=WR_IOT_STOP_CLOSE_BEGIN||
    s->close.phase!=WR_IOT_CLOSE_IDLE||
    !wr_iot_disable_services_cancel(&s->disable.services))return 0;
 wr_iot_service_guard_leave(s->guard);s->guard=0;
 s->phase=WR_IOT_STOP_CANCELLED;return 1;
}
/* Fresh configuration observation, never an RF/FIFO retirement claim or a
 * future lease. Driver release and every network stage retain their own checks. */
static int stop_closed_current(struct wr_iot_precreated_stop *s)
{
 struct wr_iot_driver_closed_result observed;
 if(!wr_iot_driver_attempt_closed(&s->attempt,&observed)||
    observed.open_token!=s->close.request.open_token||!observed.close_serial||
    (s->close_serial&&s->close_serial!=observed.close_serial))return 0;
 s->close_serial=observed.close_serial;return 1;
}
int wr_iot_precreated_stop_step(struct wr_iot_precreated_stop *s)
{
 struct wr_iot_driver_open_current_result receipt;
 if(!s)return 0;
 if(s->phase==WR_IOT_STOP_COMPLETE)return s->owner==getpid()&&!s->guard;
 if(!stop_owned(s))return 0;
 if(s->phase==WR_IOT_STOP_CLOSE_BEGIN){
  if(!wr_iot_driver_open_current_read(&s->attempt,&receipt))return 0;
  (void)wr_iot_close_controller_begin(&s->close,&s->attempt,&receipt);
  if(s->close.phase!=WR_IOT_CLOSE_IDLE)s->phase=WR_IOT_STOP_CLOSE;
  return 0;
 }
 if(s->phase==WR_IOT_STOP_CLOSE){
  if(wr_iot_close_controller_advance(&s->close))s->phase=WR_IOT_STOP_ISOLATE;
  return 0;
 }
 if(s->phase<WR_IOT_STOP_ISOLATE||s->phase>WR_IOT_STOP_COMMIT||
    s->close.phase!=WR_IOT_CLOSE_OWNER_RELEASED||!stop_closed_current(s))return 0;
 switch(s->phase){
 case WR_IOT_STOP_ISOLATE:
  if(!wr_iot_disable_services_isolate(&s->disable.services))return 0;
  break;
 case WR_IOT_STOP_SERVICES:
  if(!wr_iot_disable_apply_services(&s->disable))return 0;
  break;
 case WR_IOT_STOP_BRIDGE_DOWN:
  if(!wr_iot_bridge_set_up(0))return 0;
  break;
 case WR_IOT_STOP_DETACH:
  if(!wr_iot_bridge_detach())return 0;
  break;
 case WR_IOT_STOP_REMOVE:
  if(!wr_iot_bridge_remove())return 0;
  break;
 case WR_IOT_STOP_APPLY:
  if(!wr_iot_disable_apply_reserved(&s->disable))return 0;
  break;
 case WR_IOT_STOP_OBSERVE:
  if(if_nametoindex("br-iot")||!wr_iot_bss_is_down()||
     !wr_iot_request_disable_ready(&s->disable.services.settings))return 0;
  break;
 case WR_IOT_STOP_COMMIT:
  if(!wr_iot_disable_commit(&s->disable))return 0;
  wr_iot_service_guard_leave(s->guard);s->guard=0;
  s->phase=WR_IOT_STOP_COMPLETE;return 1;
 default:return 0;
 }
 s->phase++;return 0;
}
