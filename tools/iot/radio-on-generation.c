#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-generation.h"
#include "radio-off-observe.h"
#include "restart-main-state.h"
#include "rc-runtime.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
static int on_generation_current(struct wr_iot_on_generation *s)
{
 struct wr_iot_on_admission *a=s->admission;
 struct wr_iot_physical_stop_request r={0};struct wr_iot_rc_mode mode={0};
 unsigned char expected[64],current[64];
 return a&&a->owner==getpid()&&a->busy==1&&a->guard==1&&
  a->phase==WR_ON_ADMISSION_CAPTURED&&a->fence.owner==getpid()&&a->fence.level==1&&
  wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_off_owned&&
  wr_iot_radio_profile_owned(&a->profile)&&a->profile.files.count==1&&
  wr_iot_rc_radio_off_receipt(&r)&&
  wr_iot_physical_stop_request_encode(expected,sizeof(expected),&a->released)&&
  wr_iot_physical_stop_request_encode(current,sizeof(current),&r)&&!memcmp(expected,current,sizeof(current))&&
  wr_iot_rc_mode_read(&mode)&&mode.router==1&&mode.radio==1&&mode.mode==0&&
  wr_iot_radio_resume_down_observed(&a->released);
}
int wr_iot_on_generation_begin(struct wr_iot_on_generation *s,
 struct wr_iot_on_admission *a,const struct wr_iot_request *desired,int reload)
{
 if(!s||!a||!desired||s->owner||s->busy||s->admission||s->phase!=WR_ON_GEN_IDLE||
    a->owner!=getpid()||a->busy||a->phase!=WR_ON_ADMISSION_CAPTURED||
    a->profile.generated||a->profile.recovering||a->profile.removing||
    a->profile.files.journalled||a->profile.files.dirty||a->profile.files.pending||
    desired->enabled!=1||(reload!=0&&reload!=1)||
    !memchr(desired->ssid,0,sizeof(desired->ssid))||!memchr(desired->password,0,sizeof(desired->password))||
    wr_iot_rc_shutdown.pending)return 0;
 /* Capture-only admission cancellation is excluded before any generator call. */
 a->busy=1;s->admission=a;s->desired=*desired;
 if(!on_generation_current(s)||
    !wr_iot_generated_matches(&a->profile.files.generated[0],a->profile.files.paths[0])||
    !wr_iot_restart_profile_current(&s->desired)||wr_iot_rc_shutdown.pending){
  volatile unsigned char *p=(volatile unsigned char *)&s->desired;size_t n=sizeof(s->desired);
  while(n--)*p++=0;
  s->admission=NULL;a->busy=0;return 0;
 }
 s->owner=getpid();s->reload=reload;s->phase=WR_ON_GEN_CAPTURED;return 1;
}
int wr_iot_on_generation_abort(struct wr_iot_on_generation *s)
{
 if(!s||s->owner!=getpid()||s->busy||s->phase<WR_ON_GEN_CAPTURED||s->phase>WR_ON_GEN_RESTORING||
    !on_generation_current(s))return 0;
 s->phase=WR_ON_GEN_RESTORING;return 1;
}
int wr_iot_on_generation_step(struct wr_iot_on_generation *s)
{
 int result=0;
 if(!s||s->owner!=getpid()||s->busy||wr_iot_rc_shutdown.pending||!on_generation_current(s))return 0;
 s->busy=1;
 if(s->phase==WR_ON_GEN_CAPTURED){
  if(!s->reload)s->phase=WR_ON_GEN_GENERATED;
  else if(!s->attempted){
   s->attempted=1;s->phase=WR_ON_GEN_RESTORING;
   if(wr_iot_radio_profile_generate(&s->admission->profile,wr_iot_rc_restart_generate))s->phase=WR_ON_GEN_GENERATED;
  }
 }else if(s->phase==WR_ON_GEN_GENERATED||s->phase==WR_ON_GEN_VERIFIED){
  if(wr_iot_generated_matches(&s->admission->profile.files.generated[0],s->admission->profile.files.paths[0])&&
     wr_iot_restart_profile_current(&s->desired)&&on_generation_current(s)&&!wr_iot_rc_shutdown.pending){s->phase=WR_ON_GEN_VERIFIED;result=1;}
  else s->phase=WR_ON_GEN_RESTORING;
 }else if(s->phase==WR_ON_GEN_RESTORING){
  if(wr_iot_radio_profile_restore(&s->admission->profile)){s->phase=WR_ON_GEN_RESTORED;result=-1;}
 }else if(s->phase==WR_ON_GEN_RESTORED)
  result=wr_iot_generated_matches(&s->admission->profile.restored_file,s->admission->profile.files.paths[0])?-1:0;
 s->busy=0;return result;
}
