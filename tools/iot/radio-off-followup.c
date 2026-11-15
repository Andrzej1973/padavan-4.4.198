#define _GNU_SOURCE
#include <unistd.h>
#include <string.h>
#include "radio-off-followup.h"
#include "radio-off-state.h"
#include "radio-off-auth.h"
#include "radio-off-bridge.h"
#include "radio-off-observe.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
static int followup_owner(const struct wr_iot_radio_off_owner *off)
{
 return off&&off->owner==getpid()&&!off->busy&&off->result==1&&off->policy_ready&&
  wr_iot_physical_stop_request_valid(&off->released)&&off->released.action==WR_STOP_RELEASE&&
  wr_iot_rc_shutdown.radio_off_owned&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;
}
static int followup_current(const struct wr_iot_off_followup *s)
{
 unsigned char before[64],after[64];
 return followup_owner(s->off)&&s->policy.reload==s->off->policy.reload&&
  s->policy.stored_radio==s->off->policy.stored_radio&&
  s->policy.auth_required==s->off->policy.auth_required&&s->policy.wan==s->off->policy.wan&&
  wr_iot_physical_stop_request_encode(before,sizeof(before),&s->released)&&
  wr_iot_physical_stop_request_encode(after,sizeof(after),&s->off->released)&&
  !memcmp(before,after,sizeof(before));
}
int wr_iot_off_followup_begin(struct wr_iot_off_followup *s,const struct wr_iot_radio_off_owner *off)
{
 int token;
 if(!s||s->owner||s->busy||s->phase!=WR_OFF_FOLLOWUP_IDLE||s->profile.owner||
    !followup_owner(off))return 0;
 s->busy=1;token=wr_iot_service_guard_enter(1);
 if(token!=1){s->busy=0;return 0;}
 if(!wr_iot_radio_off_observed(&off->released)){s->busy=0;wr_iot_service_guard_leave(token);return 0;}
 s->owner=getpid();s->off=off;s->policy=off->policy;s->released=off->released;s->phase=WR_OFF_FOLLOWUP_PROFILE_BEGIN;s->busy=0;wr_iot_service_guard_leave(token);return 1;
}
enum wr_iot_off_followup_phase wr_iot_off_followup_step(struct wr_iot_off_followup *s)
{
 int result,token;enum wr_iot_off_followup_phase entered;
 if(!s||s->owner!=getpid()||s->busy||!followup_current(s))return s?s->phase:WR_OFF_FOLLOWUP_IDLE;
 s->busy=1;entered=s->phase;
 if(s->phase==WR_OFF_FOLLOWUP_PROFILE_BEGIN){
  if(wr_iot_off_profile_begin(&s->profile,s->off))s->phase=WR_OFF_FOLLOWUP_PROFILE;
 }else if(s->phase==WR_OFF_FOLLOWUP_PROFILE){
  result=wr_iot_off_profile_step(&s->profile);
  if(result==1)s->phase=WR_OFF_FOLLOWUP_STATE;
  else if(result==-1)s->phase=WR_OFF_FOLLOWUP_RETAINED;
 }else if(s->phase==WR_OFF_FOLLOWUP_STATE&&!s->state_attempted){
  token=wr_iot_service_guard_enter(1);
  if(token==1){
   if(s->profile.phase==WR_OFF_PROFILE_VERIFIED&&
      wr_iot_radio_off_observed(&s->released)&&wr_iot_rc_off_profile_current()){
    s->state_attempted=1;
    s->phase=wr_iot_rc_radio_off_state(&s->policy,&s->released)?
     WR_OFF_FOLLOWUP_BRIDGE:WR_OFF_FOLLOWUP_RETAINED;
   }
   wr_iot_service_guard_leave(token);
  }
 }
 if(entered==WR_OFF_FOLLOWUP_BRIDGE&&s->phase==WR_OFF_FOLLOWUP_BRIDGE){
  enum wr_iot_off_bridge_result detached;
  /* State mutation and bridge detach occur in separate RC windows. */
  if(s->bridge_slot>=7)s->phase=WR_OFF_FOLLOWUP_BRIDGE_VERIFY;
  else {
   detached=wr_iot_radio_off_bridge_detach(&s->released,s->bridge_slot);
   if(detached==WR_OFF_BRIDGE_DETACHED)s->bridge_slot++;
   else if(detached==WR_OFF_BRIDGE_UNCERTAIN)s->phase=WR_OFF_FOLLOWUP_RETAINED;
  }
 }
 if(entered==WR_OFF_FOLLOWUP_BRIDGE_VERIFY&&s->phase==WR_OFF_FOLLOWUP_BRIDGE_VERIFY){
  if(s->bridge_verify>=7)s->phase=WR_OFF_FOLLOWUP_AUTH;
  else if(wr_iot_radio_off_bridge_observed(&s->released,s->bridge_verify))s->bridge_verify++;
 }
 if(entered==WR_OFF_FOLLOWUP_AUTH&&s->phase==WR_OFF_FOLLOWUP_AUTH&&!s->auth_attempted){
  token=wr_iot_service_guard_enter(1);
  if(token==1){
   if(wr_iot_radio_off_observed(&s->released)){
    s->auth_attempted=1;
    s->phase=wr_iot_rc_radio_off_auth(&s->policy,&s->released)==WR_OFF_AUTH_RETURNED?
     WR_OFF_FOLLOWUP_NETWORK_PENDING:WR_OFF_FOLLOWUP_RETAINED;
   }
   wr_iot_service_guard_leave(token);
  }
 }
 if(entered==WR_OFF_FOLLOWUP_NETWORK_PENDING&&s->phase==WR_OFF_FOLLOWUP_NETWORK_PENDING){
  if(wr_iot_off_wan_begin(&s->wan,s->off))s->phase=WR_OFF_FOLLOWUP_WAN;
 }
 if(entered==WR_OFF_FOLLOWUP_WAN&&s->phase==WR_OFF_FOLLOWUP_WAN){
  if(wr_iot_off_wan_step(&s->wan))s->phase=WR_OFF_FOLLOWUP_POSTWAN;
 }
 s->busy=0;return s->phase;
}
