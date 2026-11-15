#include <unistd.h>
#include "radio-off-profile.h"
#include "radio-off-observe.h"
#include "restart-main-state.h"
#include "service-guard.h"
int wr_iot_off_profile_begin(struct wr_iot_off_profile *s,const struct wr_iot_radio_off_owner *off)
{
 int token,claimed=0;
 if(!s||!off||s->owner||s->busy||s->phase!=WR_OFF_PROFILE_IDLE||s->baseline.active||
    off->owner!=getpid()||off->busy||off->result!=1||!off->policy_ready||
    (off->policy.reload!=0&&off->policy.reload!=1))return 0;
 s->busy=1;token=wr_iot_service_guard_enter(1);if(token!=1){s->busy=0;return 0;}
 if(wr_iot_radio_off_observed(&off->released)&&wr_iot_radio_profile_take(&s->baseline)){
  s->owner=getpid();s->reload=off->policy.reload;s->released=off->released;
  s->phase=WR_OFF_PROFILE_CAPTURED;claimed=1;
 }
 s->busy=0;wr_iot_service_guard_leave(token);return claimed;
}
int wr_iot_off_profile_step(struct wr_iot_off_profile *s)
{
 int token,result=0;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 s->busy=1;token=wr_iot_service_guard_enter(1);if(token!=1){s->busy=0;return 0;}
 if(!wr_iot_radio_off_observed(&s->released))goto done;
 if(s->phase==WR_OFF_PROFILE_CAPTURED){
  if(!s->reload)s->phase=WR_OFF_PROFILE_GENERATED;
  else if(!s->attempted){
   s->attempted=1;
   s->phase=wr_iot_radio_profile_generate(&s->baseline,wr_iot_rc_restart_generate)?WR_OFF_PROFILE_GENERATED:WR_OFF_PROFILE_RESTORING;
  }
 }else if(s->phase==WR_OFF_PROFILE_GENERATED){
  s->phase=wr_iot_rc_off_profile_current()?WR_OFF_PROFILE_VERIFIED:WR_OFF_PROFILE_RESTORING;
  result=s->phase==WR_OFF_PROFILE_VERIFIED;
 }else if(s->phase==WR_OFF_PROFILE_VERIFIED)result=wr_iot_rc_off_profile_current();
 else if(s->phase==WR_OFF_PROFILE_RESTORING){
  if(wr_iot_radio_profile_restore(&s->baseline)){s->phase=WR_OFF_PROFILE_RESTORED;result=-1;}
 }else if(s->phase==WR_OFF_PROFILE_RESTORED)
  result=wr_iot_generated_matches(&s->baseline.restored_file,s->baseline.files.paths[0])?-1:0;
 done:s->busy=0;wr_iot_service_guard_leave(token);return result;
}
