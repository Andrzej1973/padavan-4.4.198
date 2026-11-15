#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-generation.h"
#include "restart-main-state.h"
#include "rc-runtime.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
static int cold_generation_current(struct wr_iot_cold_generation *s)
{
 return !s->main_may_have_started&&wr_iot_cold_admission_origin_current(s->admission);
}
int wr_iot_cold_generation_profile_current(const struct wr_iot_cold_generation *s)
{
 if(!s)return 0;
 if(s->desired.enabled==1)return wr_iot_restart_profile_current(&s->desired);
 if(s->desired.enabled!=0||s->desired.ssid[0]||s->desired.password[0])return 0;
 return wr_iot_restart_disabled_profile_current();
}
int wr_iot_cold_generation_begin(struct wr_iot_cold_generation *s,
 struct wr_iot_cold_admission *a,const struct wr_iot_request *desired,int reload)
{
 if(!s||!a||!desired||s->owner||s->busy||s->main_may_have_started||s->admission||s->phase!=WR_COLD_GEN_IDLE||
    a->owner!=getpid()||a->busy||a->phase!=WR_COLD_CAPTURED||
    a->profile.generated||a->profile.recovering||a->profile.removing||
    a->profile.files.journalled||a->profile.files.dirty||a->profile.files.pending||
    (desired->enabled!=0&&desired->enabled!=1)||
    (!desired->enabled&&(desired->ssid[0]||desired->password[0]||desired->gateway[0]||desired->mask[0]||desired->first[0]||desired->last[0]))||(reload!=0&&reload!=1)||
    !memchr(desired->ssid,0,sizeof(desired->ssid))||!memchr(desired->password,0,sizeof(desired->password))||
    wr_iot_rc_shutdown.pending)return 0;
 #define BOUNDED(field) if(!memchr(desired->field,0,sizeof(desired->field)))return 0;
 BOUNDED(gateway) BOUNDED(mask) BOUNDED(first) BOUNDED(last)
#undef BOUNDED
 if(!wr_iot_cold_admission_current(a))return 0;
 /* Capture-only admission cancellation is excluded before any generator call. */
 a->busy=1;s->admission=a;s->desired=*desired;
 if(!cold_generation_current(s)||
    !wr_iot_generated_matches(&a->profile.files.generated[0],a->profile.files.paths[0])||
    (!reload&&!wr_iot_cold_generation_profile_current(s))||wr_iot_rc_shutdown.pending){
  volatile unsigned char *p=(volatile unsigned char *)&s->desired;size_t n=sizeof(s->desired);
  while(n--)*p++=0;
  s->admission=NULL;a->busy=0;return 0;
 }
 s->owner=getpid();s->reload=reload;s->phase=WR_COLD_GEN_CAPTURED;return 1;
}
int wr_iot_cold_generation_abort(struct wr_iot_cold_generation *s)
{
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||s->phase<WR_COLD_GEN_CAPTURED||s->phase>WR_COLD_GEN_RESTORING||
    !cold_generation_current(s))return 0;
 s->phase=WR_COLD_GEN_RESTORING;return 1;
}
int wr_iot_cold_generation_step(struct wr_iot_cold_generation *s)
{
 int result=0;
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||wr_iot_rc_shutdown.pending||!cold_generation_current(s))return 0;
 s->busy=1;
 if(s->phase==WR_COLD_GEN_CAPTURED){
  if(!s->reload)s->phase=WR_COLD_GEN_GENERATED;
  else if(!s->attempted){
   s->attempted=1;s->phase=WR_COLD_GEN_RESTORING;
   if(wr_iot_radio_profile_generate(&s->admission->profile,wr_iot_rc_restart_generate))s->phase=WR_COLD_GEN_GENERATED;
  }
 }else if(s->phase==WR_COLD_GEN_GENERATED||s->phase==WR_COLD_GEN_VERIFIED){
  if(wr_iot_generated_matches(&s->admission->profile.files.generated[0],s->admission->profile.files.paths[0])&&
     wr_iot_cold_generation_profile_current(s)&&cold_generation_current(s)&&!wr_iot_rc_shutdown.pending){s->phase=WR_COLD_GEN_VERIFIED;result=1;}
  else s->phase=WR_COLD_GEN_RESTORING;
 }else if(s->phase==WR_COLD_GEN_RESTORING){
  if(wr_iot_radio_profile_restore(&s->admission->profile)){s->phase=WR_COLD_GEN_RESTORED;result=-1;}
 }else if(s->phase==WR_COLD_GEN_RESTORED)
  result=wr_iot_generated_matches(&s->admission->profile.restored_file,s->admission->profile.files.paths[0])?-1:0;
 s->busy=0;return result;
}

int wr_iot_cold_generation_origin_current(struct wr_iot_cold_generation *s)
{
 return s&&s->owner==getpid()&&!s->busy&&cold_generation_current(s);
}

int wr_iot_cold_generation_recover(struct wr_iot_cold_generation *s)
{
 int result=0;
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||
    s->phase<WR_COLD_GEN_CAPTURED||s->phase>WR_COLD_GEN_RESTORED||
    !cold_generation_current(s)||
    !wr_iot_cold_admission_origin_current(s->admission))return 0;
 s->busy=1;
 /* No generator, Main UP or guard release is reachable from recovery. */
 s->phase=WR_COLD_GEN_RESTORING;
 if(wr_iot_radio_profile_restore(&s->admission->profile)){
  s->phase=WR_COLD_GEN_RESTORED;result=-1;
 }
 s->busy=0;return result;
}
