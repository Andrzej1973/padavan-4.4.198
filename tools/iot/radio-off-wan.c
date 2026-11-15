#include <unistd.h>
#include "radio-off-wan.h"
#include "radio-off-observe.h"
#include "restart-wan-followup.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
static int off_wan_allowed(void)
{return wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;}
int wr_iot_off_wan_begin(struct wr_iot_off_wan *s,const struct wr_iot_radio_off_owner *off)
{
 if(!s||!off||s->owner||s->busy||s->attempted||s->returned||
    off->owner!=getpid()||off->busy||off->result!=1||!off->policy_ready||
    (off->policy.wan!=WR_WAN_NONE&&off->policy.wan!=WR_WAN_FULL_RESTART)||
    !wr_iot_physical_stop_request_valid(&off->released)||off->released.action!=WR_STOP_RELEASE||
    !off_wan_allowed())return 0;
 s->owner=getpid();s->policy=off->policy;s->released=off->released;return 1;
}
int wr_iot_off_wan_step(struct wr_iot_off_wan *s)
{
 int token,valid;
 if(!s||s->owner!=getpid()||s->busy||!off_wan_allowed())return 0;
 if(s->attempted)return s->returned;
 if(s->policy.wan!=WR_WAN_NONE&&s->policy.wan!=WR_WAN_FULL_RESTART)return 0;
 s->busy=1;token=wr_iot_service_guard_enter(1);
 if(token!=1){s->busy=0;return 0;}
 valid=wr_iot_radio_off_observed(&s->released)&&
  wr_iot_rc_restart_wan_current(0,s->policy.wan)&&off_wan_allowed();
 wr_iot_service_guard_leave(token);
 if(valid&&off_wan_allowed()){
  s->attempted=1;
  if(s->policy.wan==WR_WAN_FULL_RESTART)wr_iot_rc_restart_wan_submit(s->policy.wan);
  s->returned=1;
 }
 s->busy=0;return s->returned;
}
