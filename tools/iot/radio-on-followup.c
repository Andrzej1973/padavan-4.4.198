#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-followup.h"
#include "control-record.h"
#include "rc-backend.h"
#include "restart-iapp-policy.h"
#include "rc-shutdown-admission.h"
#include "radio-on-aux.h"
#include "restart-main-bridge.h"
#include "restart-guest-policy.h"
#include "restart-guest-bridge.h"
#include "restart-guest-isolation.h"
#include "restart-multicast.h"
static int on_followup_parent(struct wr_iot_on_restore *s)
{
 struct wr_iot_multicast_policy mc;struct wr_iot_restart_service_policy policy;int desired,isolate,state;
 if(!wr_iot_restart_profile_receipt_current(&s->profile_receipt)||!wr_iot_on_aux_down_current()||
    !wr_iot_restart_main_bridge_current()||!wr_iot_rc_restart_guest_policy(&desired)||desired!=s->guest.desired||
    !wr_iot_rc_restart_guest_isolation_policy(&isolate)||isolate!=s->guest.isolate||
    !wr_iot_restart_guest_admin_state(&state)||state!=desired||
    (desired&&(!wr_iot_restart_guest_bridge_current()||!wr_iot_restart_guest_isolation_current(isolate)))||
    !wr_iot_rc_restart_multicast_policy(&mc)||mc.required!=s->multicast.policy.required||
    mc.enabled!=s->multicast.policy.enabled||mc.guest!=s->multicast.policy.guest||
    (mc.required&&(!wr_iot_restart_multicast_current(0,mc.enabled)||
      (mc.guest&&!wr_iot_restart_multicast_current(1,mc.enabled))))||
    !wr_iot_rc_restart_service_policy(&policy)||policy.enterprise!=s->services.policy.enterprise||
    policy.kick_rssi!=s->services.policy.kick_rssi||policy.assoc_rssi!=s->services.policy.assoc_rssi||
    !wr_iot_rc_restart_auth_process_current(&policy))return 0;
 return 1;
}
static int on_enabled_followup_network(struct wr_iot_on_restore *s)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_result r={0};unsigned i;int guard,ok;
 if(!s->handoff_created||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_off_owned)return 0;
 for(i=0;i<16;i++){r.id[2*i]=hex[s->open_id[i]>>4];r.id[2*i+1]=hex[s->open_id[i]&15];}
 r.created=s->handoff_created;r.state=WR_IOT_RESULT_APPLIED;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=on_followup_parent(s)&&wr_iot_rc_backend_observed(&r)&&on_followup_parent(s)&&
  !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;
 wr_iot_service_guard_leave(guard);return ok;
}
static int on_followup_network(struct wr_iot_on_restore *s,
 int (*observe)(struct wr_iot_on_restore *,void *),void *context)
{
 int guard,ok;
 if(!observe)return on_enabled_followup_network(s);
 if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=on_followup_parent(s)&&observe(s,context)&&on_followup_parent(s)&&
  !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;
 wr_iot_service_guard_leave(guard);return ok;
}
static int on_followup_step(struct wr_iot_on_restore *s,
 int (*observe)(struct wr_iot_on_restore *,void *),void *context)

{
 int result=0,terminal;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->phase==WR_ON_RESTORE_DONE)return on_followup_network(s,observe,context);
 s->busy=1;
 /* Drain existing child even while its terminal fence/admission is active. */
 if(s->phase==WR_ON_RESTORE_IAPP){
  terminal=wr_iot_terminal_iapp_step(&s->terminal);
  if(terminal<0)s->phase=WR_ON_RESTORE_RETAINED;
  else if(terminal==1&&wr_iot_iapp_child_closed(&s->child)&&s->child.result==1&&
          !s->terminal.child&&!s->terminal.guard&&!s->terminal.fence.owner&&
          !s->terminal.fence.level&&on_followup_network(s,observe,context)){
   s->phase=WR_ON_RESTORE_DONE;result=1;
  }
  goto done;
 }
 if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned)goto done;
 if(s->phase==WR_ON_RESTORE_RELEASED){
  if(s->generation.admission||s->generation.phase!=WR_ON_GEN_COMMITTED||
     s->wan.owner!=getpid()||s->wan.radio_on!=1||s->wan.attempted||s->wan.returned)goto done;
  s->phase=WR_ON_RESTORE_WAN;goto done;
 }
 if(s->phase==WR_ON_RESTORE_WAN){
  if(!wr_iot_wan_followup_step(&s->wan)||!on_followup_network(s,observe,context))goto done;
  if(!s->led_attempted){s->led_attempted=1;s->led_returned=wr_iot_rc_restart_led_on()==1;}
  if(!s->led_returned){s->phase=WR_ON_RESTORE_RETAINED;goto done;}
  s->phase=WR_ON_RESTORE_IAPP_PENDING;goto done;
 }
#if WR_IOT_IAPP_POLICY_PREPARED
 if(s->phase==WR_ON_RESTORE_IAPP_PENDING&&s->led_returned&&on_followup_network(s,observe,context)&&
    !s->terminal.owner&&wr_iot_terminal_iapp_begin(&s->terminal,&s->child))s->phase=WR_ON_RESTORE_IAPP;
#endif
 done:s->busy=0;return result;
}

int wr_iot_on_followup_step(struct wr_iot_on_restore *s)
{return on_followup_step(s,NULL,NULL);}
int wr_iot_on_followup_observed(struct wr_iot_on_restore *s,
 int (*observe)(struct wr_iot_on_restore *,void *),void *context)
{return observe&&context?on_followup_step(s,observe,context):0;}
