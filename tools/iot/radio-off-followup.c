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
#include "restart-iapp-policy.h"
static int followup_owner_scope(const struct wr_iot_radio_off_owner *off,int finalizing)
{
 return off&&off->owner==getpid()&&!off->busy&&off->result==1&&off->policy_ready&&
  wr_iot_physical_stop_request_valid(&off->released)&&off->released.action==WR_STOP_RELEASE&&
  wr_iot_rc_shutdown.radio_off_owned&&wr_iot_rc_shutdown.active==finalizing&&
  (finalizing||!wr_iot_rc_shutdown.pending);
}
static int followup_owner(const struct wr_iot_radio_off_owner *off)
{return followup_owner_scope(off,0);}
static int followup_current_scope(const struct wr_iot_off_followup *s,int finalizing)
{
 unsigned char before[64],after[64];
 return followup_owner_scope(s->off,finalizing)&&s->policy.reload==s->off->policy.reload&&
  s->policy.stored_radio==s->off->policy.stored_radio&&
  s->policy.auth_required==s->off->policy.auth_required&&s->policy.wan==s->off->policy.wan&&
  wr_iot_physical_stop_request_encode(before,sizeof(before),&s->released)&&
  wr_iot_physical_stop_request_encode(after,sizeof(after),&s->off->released)&&
  !memcmp(before,after,sizeof(before));
}
static int followup_current(const struct wr_iot_off_followup *s)
{return followup_current_scope(s,0);}
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
 if(!s||s->owner!=getpid()||s->busy)return s?s->phase:WR_OFF_FOLLOWUP_IDLE;
 /* Once child/fence is owned, drain through the terminal controller even
  * while its admission is active or a normal shutdown is pending. */
 if(s->phase==WR_OFF_FOLLOWUP_IAPP){
  s->busy=1;result=wr_iot_terminal_iapp_step(&s->iapp);
  if(result==1)s->phase=WR_OFF_FOLLOWUP_FINAL_PENDING;
  else if(result==-1)s->phase=WR_OFF_FOLLOWUP_RETAINED;
  s->busy=0;return s->phase;
 }
 if(!followup_current(s))return s->phase;
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
      wr_iot_radio_off_observed(&s->released)&&wr_iot_off_profile_current(&s->profile)){
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
 if(entered==WR_OFF_FOLLOWUP_POSTWAN&&s->phase==WR_OFF_FOLLOWUP_POSTWAN){
  token=wr_iot_service_guard_enter(1);
  if(token==1){
   if(wr_iot_radio_off_observed(&s->released)&&wr_iot_off_profile_current(&s->profile)){
    if(s->postwan_slot>=7)s->phase=WR_OFF_FOLLOWUP_IAPP_PENDING;
    else if(wr_iot_radio_off_bridge_observed(&s->released,s->postwan_slot))s->postwan_slot++;
   }else s->postwan_slot=0;
   wr_iot_service_guard_leave(token);
  }
 }
#if WR_IOT_IAPP_POLICY_PREPARED
 if(entered==WR_OFF_FOLLOWUP_IAPP_PENDING&&s->phase==WR_OFF_FOLLOWUP_IAPP_PENDING){
  token=wr_iot_service_guard_enter(1);
  if(token==1){
   result=wr_iot_radio_off_observed(&s->released)&&wr_iot_off_profile_current(&s->profile);
   wr_iot_service_guard_leave(token);
   if(result&&followup_current(s)&&wr_iot_terminal_iapp_begin(&s->iapp,&s->child))
    s->phase=WR_OFF_FOLLOWUP_IAPP;
  }
 }
#endif
 s->busy=0;return s->phase;
}

int wr_iot_off_followup_final_current(const struct wr_iot_off_followup *s)
{
 const struct wr_iot_radio_profile_state *p;unsigned slot;int finalizing;
 int (*observe)(const struct wr_iot_physical_stop_request *);
 if(!s)return 0;
 finalizing=s->phase==WR_OFF_FOLLOWUP_FINALIZING;
 if(finalizing&&(s->finish_off!=s->off||s->finish_guard!=1||
    s->finish_fence.owner!=getpid()||s->finish_fence.level!=1))return 0;
 observe=finalizing?wr_iot_radio_recovery_down_observed:wr_iot_radio_off_observed;
 if(!s||s->owner!=getpid()||s->busy||(s->phase!=WR_OFF_FOLLOWUP_FINAL_PENDING&&!finalizing)||
    !followup_current_scope(s,finalizing)||s->bridge_slot!=7||s->bridge_verify!=7||s->postwan_slot!=7||
    !s->state_attempted||!s->auth_attempted||!s->wan.attempted||!s->wan.returned||
    s->wan.busy||s->wan.owner!=getpid()||s->iapp.owner!=getpid()||s->iapp.busy||
    s->iapp.result!=1||s->iapp.guard||s->iapp.child||s->iapp.fence.owner||s->iapp.fence.level||
    !wr_iot_iapp_child_closed(&s->child)||s->child.result!=1||
    s->profile.owner!=getpid()||s->profile.busy||s->profile.phase!=WR_OFF_PROFILE_VERIFIED)return 0;
 p=&s->profile.baseline;
 if(!wr_iot_radio_profile_guard()||p->owner!=getpid()||!p->active||p->recovering||
    p->recovered||p->removing||p->files.count!=1||p->files.pending||p->files.restored||
    (s->policy.reload&&(!p->generated||!p->files.sealed))||
    (!s->policy.reload&&(p->generated||p->files.journalled))||
    !wr_iot_generated_matches(&p->files.generated[0],p->files.paths[0])||
    !observe(&s->released)||!wr_iot_off_profile_current(&s->profile))return 0;
 for(slot=0;slot<7;slot++)if(!(finalizing?wr_iot_radio_off_bridge_final_observed(&s->released,slot):
  wr_iot_radio_off_bridge_observed(&s->released,slot)))return 0;
 return followup_current_scope(s,finalizing)&&observe(&s->released)&&
  wr_iot_generated_matches(&p->files.generated[0],p->files.paths[0])&&wr_iot_radio_profile_guard();
}

static void off_finish_wipe(void *data,size_t size)
{volatile unsigned char *p=data;while(size--)*p++=0;}
static void off_finish_cleanup(void *context)
{
 struct wr_iot_off_followup *s=context;
 wr_iot_bundle_release(&s->profile.baseline.files);
 off_finish_wipe(&s->profile,sizeof(s->profile));
 off_finish_wipe(s->finish_off,sizeof(*s->finish_off));
 s->finish_off=NULL;s->off=NULL;
 wr_iot_rc_shutdown.radio_off_owned=0;
 s->phase=WR_OFF_FOLLOWUP_DONE;s->busy=0;
 if(s->finish_publish){s->finish_publish(s,s->finish_context);s->finish_published=1;}
 wr_iot_service_guard_leave(s->finish_guard);s->finish_guard=0;
}
int wr_iot_off_followup_finish(struct wr_iot_off_followup *s,struct wr_iot_radio_off_owner *off)
{
 int token;
 if(!s||!off||s->owner!=getpid()||s->busy)return 0;
 if(s->phase==WR_OFF_FOLLOWUP_FINALIZING){
  if(s->finish_off!=off||s->off!=off||s->finish_guard!=1||
     s->finish_fence.owner!=getpid()||s->finish_fence.level!=1||!wr_iot_rc_shutdown.active)return 0;
 }else{
  if(s->off!=off||s->finish_off||s->finish_guard||s->finish_fence.owner||s->finish_fence.level)return 0;
  token=wr_iot_service_guard_enter(1);if(token!=1)return 0;
  if(!wr_iot_off_followup_final_current(s)){
   wr_iot_service_guard_leave(token);return 0;
  }
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  {
   struct wr_iot_restart_profile_receipt receipt={0};
   const struct wr_iot_saved_bundle *files=&s->profile.baseline.files;size_t length;
   if(!memchr(files->paths[0],0,sizeof(files->paths[0]))){wr_iot_service_guard_leave(token);return 0;}
   length=strlen(files->paths[0]);if(!length||length>=sizeof(receipt.path)){wr_iot_service_guard_leave(token);return 0;}
   memcpy(receipt.path,files->paths[0],length+1);receipt.file=files->generated[0];
   receipt.owner=getpid();receipt.valid=1;
   if(!wr_iot_restart_profile_receipt_current(&receipt)){wr_iot_service_guard_leave(token);return 0;}
   s->profile_receipt=receipt;
  }
#endif
  if(wr_iot_rc_shutdown.normal_route_requested?
     !wr_iot_radio_stop_fence_begin_routed_shutdown(&s->finish_fence):
     !wr_iot_radio_stop_fence_begin(&s->finish_fence)){
   wr_iot_service_guard_leave(token);return 0;
  }
  s->finish_off=off;s->finish_guard=token;s->phase=WR_OFF_FOLLOWUP_FINALIZING;
 }
 /* Retry under the same retained fence reobserves the full final state. No
  * bridge detach, generation, WAN or child command is replayed here. */
 if(!wr_iot_off_followup_final_current(s)||
    (!!s->finish_prepare!=!!s->finish_publish)||s->finish_published||
    (s->finish_prepare&&!s->finish_prepare(s,s->finish_context)))return 0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!wr_iot_restart_profile_receipt_current(&s->profile_receipt))return 0;
#endif
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&s->finish_fence,off_finish_cleanup,s)){s->busy=0;return 0;}
 return s->phase==WR_OFF_FOLLOWUP_DONE;
}
