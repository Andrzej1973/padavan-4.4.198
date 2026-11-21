#define _GNU_SOURCE
#include <unistd.h>
#include "radio-off-profile.h"
#include "radio-off-observe.h"
#include "restart-main-state.h"
#include "service-guard.h"
#include "generation-profile.h"
int wr_iot_off_profile_begin(struct wr_iot_off_profile *s,const struct wr_iot_radio_off_owner *off)
{
 int token,claimed=0;
 if(!s||!off||s->self||s->owner||s->busy||s->phase!=WR_OFF_PROFILE_IDLE||s->baseline.active||
    off->owner!=getpid()||off->busy||off->result!=1||!off->policy_ready||
    (off->policy.reload!=0&&off->policy.reload!=1))return 0;
 s->busy=1;token=wr_iot_service_guard_enter(1);if(token!=1){s->busy=0;return 0;}
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(s->config_revision.owner||s->config_revision.self)goto done;
 if(!off->policy.reload){
  if((off->profile_binding.kind!=WR_PROFILE_BACKEND_ACTIVE&&off->profile_binding.kind!=WR_PROFILE_BACKEND_REBIND_ACTIVE)||
     off->profile_binding.identity.adapter_epoch!=off->released.epoch||
     off->profile_binding.identity.device_generation!=off->released.generation||
     !off->profile_binding.created||!memchr(off->profile_binding.id,0,sizeof(off->profile_binding.id))||
     !wr_iot_control_id(off->profile_binding.id)||off->profile_receipt.file.existed!=1||
     off->profile_receipt.file.metadata.st_size<=0||
     !wr_iot_restart_profile_receipt_current(&off->profile_receipt))goto done;
 }
 if(off->policy.reload){
  struct wr_iot_saved_config provisioning={0};char id[33]={0};unsigned i;
  static const char hex[]="0123456789abcdef";int captured;
  for(i=0;i<16;i++){id[2*i]=hex[off->released.nonce[i]>>4];id[2*i+1]=hex[off->released.nonce[i]&15];}
  captured=wr_iot_radio_off_observed(&off->released)&&
   wr_iot_generation_config_capture(&s->config_revision,id,
    off->released.closed_serial,&provisioning);
  wr_iot_saved_wipe(&provisioning,sizeof(provisioning));
  if(!captured)goto done;
 }
#endif
 if(wr_iot_radio_off_observed(&off->released)&&wr_iot_radio_profile_take(&s->baseline)){
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  if(!off->policy.reload){
   if(!wr_iot_restart_profile_receipt_current(&off->profile_receipt)){
    (void)wr_iot_radio_profile_cancel(&s->baseline);goto done;
   }
   s->history_binding=off->profile_binding;s->history_profile=off->profile_receipt;
  }
#endif
  s->self=s;s->owner=getpid();s->reload=off->policy.reload;s->released=off->released;
  s->phase=WR_OFF_PROFILE_CAPTURED;claimed=1;
 }
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!claimed&&s->config_revision.owner)(void)wr_iot_generation_config_release(&s->config_revision);
 done:
#endif
 s->busy=0;wr_iot_service_guard_leave(token);return claimed;
}
int wr_iot_off_profile_step(struct wr_iot_off_profile *s)
{
 int token,result=0;
 if(!s||s->self!=s||s->owner!=getpid()||s->busy)return 0;
 s->busy=1;token=wr_iot_service_guard_enter(1);if(token!=1){s->busy=0;return 0;}
 if(!wr_iot_radio_off_observed(&s->released))goto done;
 if(s->phase==WR_OFF_PROFILE_CAPTURED){
  if(!s->reload)s->phase=WR_OFF_PROFILE_GENERATED;
  else if(!s->attempted){
   s->attempted=1;
   s->phase=WR_OFF_PROFILE_RESTORING;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
   /* No unbound desired reread or retry after revision drift. */
   if(wr_iot_generation_profile_enter(&s->config_revision)){
    int generated=wr_iot_radio_profile_generate(&s->baseline,wr_iot_rc_restart_generate);
    int released=wr_iot_generation_profile_leave(&s->config_revision);
    if(generated&&released)s->phase=WR_OFF_PROFILE_GENERATED;
   }
#else
   if(wr_iot_radio_profile_generate(&s->baseline,wr_iot_rc_restart_generate))s->phase=WR_OFF_PROFILE_GENERATED;
#endif
  }
 }else if(s->phase==WR_OFF_PROFILE_GENERATED){
  s->phase=wr_iot_off_profile_current(s)?WR_OFF_PROFILE_VERIFIED:WR_OFF_PROFILE_RESTORING;
  result=s->phase==WR_OFF_PROFILE_VERIFIED;
 }else if(s->phase==WR_OFF_PROFILE_VERIFIED)result=wr_iot_off_profile_current(s);
 else if(s->phase==WR_OFF_PROFILE_RESTORING){
  if(wr_iot_radio_profile_restore(&s->baseline)){s->phase=WR_OFF_PROFILE_RESTORED;result=-1;}
 }else if(s->phase==WR_OFF_PROFILE_RESTORED)
  result=wr_iot_generated_matches(&s->baseline.restored_file,s->baseline.files.paths[0])?-1:0;
 done:s->busy=0;wr_iot_service_guard_leave(token);return result;
}
