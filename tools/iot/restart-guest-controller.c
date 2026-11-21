#define _GNU_SOURCE
#include <unistd.h>
#include "restart-guest-controller.h"
#include "restart-guest-policy.h"
#include "restart-guest-bridge.h"
#include "restart-guest-isolation.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
int wr_iot_restart_guest_begin(struct wr_iot_restart_guest *s,struct wr_iot_restart_main *main)
{
 int desired,isolate;
 if(!s||!main||s->owner||s->busy||s->phase!=WR_GUEST_IDLE||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_restart_main_lan_step(main)||!wr_iot_rc_restart_guest_policy(&desired)||
    (desired!=0&&desired!=1)||!wr_iot_rc_restart_guest_isolation_policy(&isolate)||
    (isolate!=0&&isolate!=1)||wr_iot_rc_shutdown.pending)return 0;
 s->owner=getpid();s->main=main;s->desired=desired;s->isolate=isolate;
 if(!desired){s->phase=WR_GUEST_POLICY_OFF;return 1;}
 s->phase=WR_GUEST_BRIDGE;return 1;
}
int wr_iot_restart_guest_step(struct wr_iot_restart_guest *s)
{
 int desired,isolate,state,fd,ok=0;enum wr_iot_restart_up_result result;
 if(!s||s->owner!=getpid()||s->busy||!s->main||
    (s->phase<WR_GUEST_BRIDGE||s->phase>WR_GUEST_DOWN_OBSERVED||s->phase==WR_GUEST_NO_SUBMISSION)||
    !wr_iot_rc_shutdown.active)return 0;
 s->busy=1;
 if(s->phase==WR_GUEST_RECOVER_DOWN||s->phase==WR_GUEST_DOWN_OBSERVED)goto recover;
 if(wr_iot_rc_shutdown.pending)goto invalid;
 if(!wr_iot_restart_main_lan_step(s->main)||!wr_iot_rc_restart_guest_policy(&desired)||
    desired!=s->desired||!wr_iot_rc_restart_guest_isolation_policy(&isolate)||isolate!=s->isolate)
  goto invalid;
 if(s->phase==WR_GUEST_BRIDGE){
  if(!s->bridge_attempted){s->bridge_attempted=1;(void)wr_iot_restart_guest_bridge_attach();}
  if(wr_iot_restart_guest_admin_state(&state)&&!state&&wr_iot_restart_guest_bridge_current())
   s->phase=WR_GUEST_ISOLATE;
  goto done;
 }
 if(s->phase==WR_GUEST_ISOLATE){
  if(wr_iot_restart_guest_bridge_current()&&wr_iot_restart_guest_isolation_prepare(s->isolate))
   s->phase=WR_GUEST_OPEN;
  goto done;
 }
 if(s->phase==WR_GUEST_OPEN){
  if(!wr_iot_restart_guest_bridge_current()||!wr_iot_restart_guest_isolation_current(s->isolate))goto done;
  s->phase=WR_GUEST_WAIT;result=wr_iot_restart_guest_up();
  if(result==WR_RESTART_UP_NOT_SUBMITTED)s->phase=WR_GUEST_NO_SUBMISSION;
  goto done;
 }
 if(wr_iot_restart_guest_admin_state(&state)&&state==s->desired&&
    (!s->desired||(wr_iot_restart_guest_bridge_current()&&wr_iot_restart_guest_isolation_current(s->isolate)))&&
    wr_iot_restart_main_lan_step(s->main)&&!wr_iot_rc_shutdown.pending){
  if(s->desired)s->phase=WR_GUEST_ADMIN_UP;
  ok=1;goto done;
 }
 if(s->phase==WR_GUEST_WAIT||s->phase==WR_GUEST_ADMIN_UP)goto invalid;
 goto done;
 invalid:
 /* Only our submitted UP permits recovery mutation. Pre-OPEN refusal and
  * policy-OFF observations never acquire a foreign Guest interface. */
 if(s->phase!=WR_GUEST_WAIT&&s->phase!=WR_GUEST_ADMIN_UP)goto done;
 s->phase=WR_GUEST_RECOVER_DOWN;
 recover:
 /* Recovery bypasses failed Main/policy checks, never the outer service lock.
  * Leave the attempt unused if ownership cannot be demonstrated. */
 s->phase=WR_GUEST_RECOVER_DOWN;
 fd=wr_iot_service_guard_dup();if(fd<0)goto done;
 if(close(fd))goto done;
 if(!s->down_attempted){
  s->down_attempted=1;
  (void)wr_iot_restart_guest_down();
 }
 s->phase=WR_GUEST_RECOVER_DOWN;
 if(wr_iot_restart_guest_admin_state(&state)&&!state)
  s->phase=WR_GUEST_DOWN_OBSERVED;
 /* Recovery never grants readiness, reopens Guest or releases Main ownership.
  * Administrative DOWN does not prove firmware/DMA/TxS retirement. */
 done:
 s->busy=0;return ok;
}
