#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-generation.h"
#include "generation-profile.h"
#include "radio-off-observe.h"
#include "restart-main-state.h"
#include "rc-runtime.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
static int on_generation_current(struct wr_iot_on_generation *s,int require_down)
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
  wr_iot_rc_radio_on_mode_read(&mode)&&mode.router==1&&mode.radio==1&&mode.mode==0&&
  (!require_down||wr_iot_radio_resume_down_observed(&a->released));
}
int wr_iot_on_generation_profile_current(const struct wr_iot_on_generation *s)
{
 if(!s)return 0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(s->config_revision.present){
  struct wr_iot_request profile=s->provisioning.profile;int ok;
  if(!wr_iot_generation_config_owned(&s->config_revision))return 0;
  profile.enabled=1;ok=wr_iot_restart_profile_file_current(&profile);
  wr_iot_saved_wipe(&profile,sizeof(profile));return ok;
 }
#endif
 if(s->desired.enabled==1)return wr_iot_restart_profile_current(&s->desired);
 if(s->desired.enabled!=0||s->desired.ssid[0]||s->desired.password[0])return 0;
 return wr_iot_restart_disabled_profile_current();
}
int wr_iot_on_generation_begin(struct wr_iot_on_generation *s,
 struct wr_iot_on_admission *a,const struct wr_iot_request *desired,int reload)
{
 if(!s||!a||!desired||s->owner||s->busy||s->main_may_have_started||s->admission||s->phase!=WR_ON_GEN_IDLE||
    a->owner!=getpid()||a->busy||a->phase!=WR_ON_ADMISSION_CAPTURED||
    a->profile.generated||a->profile.recovering||a->profile.removing||
    a->profile.files.journalled||a->profile.files.dirty||a->profile.files.pending||
    (desired->enabled!=0&&desired->enabled!=1)||
    (!desired->enabled&&(desired->ssid[0]||desired->password[0]))||(reload!=0&&reload!=1)||
    !memchr(desired->ssid,0,sizeof(desired->ssid))||!memchr(desired->password,0,sizeof(desired->password))||
    wr_iot_rc_shutdown.pending)return 0;
 /* Capture-only admission cancellation is excluded before any generator call. */
 a->busy=1;s->admission=a;s->desired=*desired;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 {
  char id[33]={0};unsigned i;int valid;static const char hex[]="0123456789abcdef";
  for(i=0;i<16;i++){id[2*i]=hex[a->released.nonce[i]>>4];id[2*i+1]=hex[a->released.nonce[i]&15];}
  valid=on_generation_current(s,1)&&wr_iot_generation_config_capture(&s->config_revision,
   id,a->released.closed_serial,&s->provisioning);
  if(valid&&s->config_revision.present){
   const struct wr_iot_request *profile=&s->provisioning.profile;
   valid=profile->enabled==desired->enabled;
#define ON_CONFIG_SAME(f) if(desired->enabled&&strcmp(profile->f,desired->f))valid=0;
   ON_CONFIG_SAME(ssid) ON_CONFIG_SAME(password) ON_CONFIG_SAME(gateway)
   ON_CONFIG_SAME(mask) ON_CONFIG_SAME(first) ON_CONFIG_SAME(last)
#undef ON_CONFIG_SAME
  }
  if(!valid){
   if(s->config_revision.owner)(void)wr_iot_generation_config_release(&s->config_revision);
   wr_iot_saved_wipe(&s->provisioning,sizeof(s->provisioning));
   wr_iot_saved_wipe(&s->desired,sizeof(s->desired));s->admission=NULL;a->busy=0;return 0;
  }
 }
#endif
 if(!on_generation_current(s,1)||
    !wr_iot_generated_matches(&a->profile.files.generated[0],a->profile.files.paths[0])||
    (!reload&&!wr_iot_on_generation_profile_current(s))||wr_iot_rc_shutdown.pending){
  volatile unsigned char *p=(volatile unsigned char *)&s->desired;size_t n=sizeof(s->desired);
  while(n--)*p++=0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  (void)wr_iot_generation_config_release(&s->config_revision);
  wr_iot_saved_wipe(&s->provisioning,sizeof(s->provisioning));
#endif
  s->admission=NULL;a->busy=0;return 0;
 }
 s->owner=getpid();s->reload=reload;s->phase=WR_ON_GEN_CAPTURED;return 1;
}
int wr_iot_on_generation_abort(struct wr_iot_on_generation *s)
{
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||s->phase<WR_ON_GEN_CAPTURED||s->phase>WR_ON_GEN_RESTORING||
    !on_generation_current(s,1))return 0;
 s->phase=WR_ON_GEN_RESTORING;return 1;
}
int wr_iot_on_generation_step(struct wr_iot_on_generation *s)
{
 int result=0;
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||wr_iot_rc_shutdown.pending||!on_generation_current(s,1))return 0;
 s->busy=1;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!wr_iot_generation_config_owned(&s->config_revision)){s->busy=0;return 0;}
 if(s->phase<=WR_ON_GEN_VERIFIED&&!wr_iot_generation_config_current(
    &s->config_revision,s->config_revision.id,s->config_revision.created))s->phase=WR_ON_GEN_RESTORING;
#endif
 if(s->phase==WR_ON_GEN_CAPTURED){
  if(!s->reload)s->phase=WR_ON_GEN_GENERATED;
  else if(!s->attempted){
   s->attempted=1;s->phase=WR_ON_GEN_RESTORING;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
   if(wr_iot_generation_profile_enter(&s->config_revision)){
    int generated=wr_iot_radio_profile_generate(&s->admission->profile,wr_iot_rc_restart_generate);
    int released=wr_iot_generation_profile_leave(&s->config_revision);
    if(generated&&released)s->phase=WR_ON_GEN_GENERATED;
   }
#else
   if(wr_iot_radio_profile_generate(&s->admission->profile,wr_iot_rc_restart_generate))s->phase=WR_ON_GEN_GENERATED;
#endif
  }
 }else if(s->phase==WR_ON_GEN_GENERATED||s->phase==WR_ON_GEN_VERIFIED){
  if(wr_iot_generated_matches(&s->admission->profile.files.generated[0],s->admission->profile.files.paths[0])&&
     wr_iot_on_generation_profile_current(s)&&on_generation_current(s,1)&&
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
     wr_iot_generation_config_current(&s->config_revision,s->config_revision.id,s->config_revision.created)&&
#endif
     !wr_iot_rc_shutdown.pending){s->phase=WR_ON_GEN_VERIFIED;result=1;}
  else s->phase=WR_ON_GEN_RESTORING;
 }else if(s->phase==WR_ON_GEN_RESTORING){
  if(wr_iot_radio_profile_restore(&s->admission->profile)){s->phase=WR_ON_GEN_RESTORED;result=-1;}
 }else if(s->phase==WR_ON_GEN_RESTORED)
  result=wr_iot_generated_matches(&s->admission->profile.restored_file,s->admission->profile.files.paths[0])?-1:0;
 s->busy=0;return result;
}

int wr_iot_on_generation_origin_current(struct wr_iot_on_generation *s)
{
 return s&&s->owner==getpid()&&!s->busy&&on_generation_current(s,0);
}

int wr_iot_on_generation_recover(struct wr_iot_on_generation *s)
{
 int result=0;
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||
    s->phase<WR_ON_GEN_CAPTURED||s->phase>WR_ON_GEN_RESTORED||
    !on_generation_current(s,0)||
    !wr_iot_radio_recovery_down_observed(&s->admission->released))return 0;
 s->busy=1;
 /* No generator, Main UP or guard release is reachable from recovery. */
 s->phase=WR_ON_GEN_RESTORING;
 if(wr_iot_radio_profile_restore(&s->admission->profile)){
  s->phase=WR_ON_GEN_RESTORED;result=-1;
 }
 s->busy=0;return result;
}
