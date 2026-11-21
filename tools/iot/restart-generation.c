#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "restart-generation.h"
#include "generation-profile.h"
#include "restart-profile.h"
#include "restart-main-state.h"
#include "rc-shutdown-admission.h"
static void generation_wipe(void *data,size_t length)
{volatile unsigned char *p=data;while(length--)*p++=0;}
static int origin_valid(const struct wr_iot_rc_physical_resume *r)
{
 if(r&&r->origin==WR_PHYSICAL_ORIGIN_INITIAL){
  struct wr_iot_request empty={0};
  if(r->intent.restart!=1||r->intent.radio_on!=1||r->intent.reload>1||
     r->physical.action||r->initial.action!=WR_STOP_RELEASE||
     !wr_iot_physical_initial_valid(&r->initial,0))return 0;
  if(!r->desired.enabled)return !r->resume_needed&&!memcmp(&r->desired,&empty,sizeof(empty));
  if(r->desired.enabled!=1||r->resume_needed!=1)return 0;
#define INITIAL_BOUNDED(f) if(!memchr(r->desired.f,0,sizeof(r->desired.f)))return 0;
  INITIAL_BOUNDED(ssid) INITIAL_BOUNDED(password) INITIAL_BOUNDED(gateway)
  INITIAL_BOUNDED(mask) INITIAL_BOUNDED(first) INITIAL_BOUNDED(last)
#undef INITIAL_BOUNDED
  return 1;
 }
 if(!r||r->origin!=WR_PHYSICAL_ORIGIN_CLOSE||r->intent.restart!=1||r->intent.radio_on!=1||r->intent.reload>1||
    r->resume_needed!=1||r->desired.enabled!=1||r->physical.action!=WR_STOP_RELEASE||
    !wr_iot_physical_stop_request_valid(&r->physical))return 0;
#define BOUNDED(f) if(!memchr(r->desired.f,0,sizeof(r->desired.f)))return 0;
 BOUNDED(ssid) BOUNDED(password) BOUNDED(gateway) BOUNDED(mask) BOUNDED(first) BOUNDED(last)
#undef BOUNDED
 return 1;
}
static int physical_origin_equal(const struct wr_iot_rc_physical_resume *a,
 const struct wr_iot_rc_physical_resume *b)
{
 unsigned char left[64],right[64];
 if(!a||!b||a->origin!=b->origin)return 0;
 if(a->origin==WR_PHYSICAL_ORIGIN_INITIAL)
  return wr_iot_physical_initial_encode(left,64,&a->initial,0)&&
   wr_iot_physical_initial_encode(right,64,&b->initial,0)&&!memcmp(left,right,64);
 if(a->origin!=WR_PHYSICAL_ORIGIN_CLOSE)return 0;
 return wr_iot_physical_stop_request_encode(left,64,&a->physical)&&
  wr_iot_physical_stop_request_encode(right,64,&b->physical)&&!memcmp(left,right,64);
}
static int generation_profile_current(const struct wr_iot_rc_physical_resume *r)
{return r->origin==WR_PHYSICAL_ORIGIN_INITIAL?(r->desired.enabled?wr_iot_restart_initial_enabled_profile_current(&r->desired):wr_iot_restart_disabled_profile_current()):wr_iot_restart_profile_current(&r->desired);}
static int generation_disabled(int unused)
{(void)unused;return wr_iot_rc_restart_generate(1);}
static int origin_current(const struct wr_iot_rc_physical_resume *expected)
{
 struct wr_iot_rc_physical_resume current={0};int ok=0;
 if(!origin_valid(expected)||!wr_iot_rc_shutdown.active||!wr_iot_radio_profile_guard()||
    !wr_iot_rc_physical_resume_read(&current)||!origin_valid(&current))goto done;
 if(expected->desired.enabled!=current.desired.enabled||expected->resume_needed!=current.resume_needed||
    expected->intent.restart!=current.intent.restart||expected->intent.radio_on!=current.intent.radio_on||
    expected->intent.reload!=current.intent.reload||
    !physical_origin_equal(expected,&current))goto done;
#define SAME(f) if(strcmp(expected->desired.f,current.desired.f))goto done;
 SAME(ssid) SAME(password) SAME(gateway) SAME(mask) SAME(first) SAME(last)
#undef SAME
 ok=1;
 done:generation_wipe(&current,sizeof(current));return ok;
}
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
static int restart_config_profile_current(const struct wr_iot_restart_generation *s)
{
 struct wr_iot_request profile=s->provisioning.profile;int ok;
 profile.enabled=1;
 ok=wr_iot_restart_profile_file_current(&profile);
 wr_iot_saved_wipe(&profile,sizeof(profile));return ok;
}
static int restart_config_take(struct wr_iot_restart_generation *s)
{
 const unsigned char *nonce=s->origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?
  s->origin.initial.nonce:s->origin.physical.nonce;
 unsigned long long serial=s->origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?
  s->origin.initial.idle_serial:s->origin.physical.closed_serial;
 char id[33]={0};unsigned i;static const char hex[]="0123456789abcdef";
 for(i=0;i<16;i++){id[2*i]=hex[nonce[i]>>4];id[2*i+1]=hex[nonce[i]&15];}
 if(!wr_iot_generation_config_capture(&s->config_revision,id,serial,&s->provisioning))return 0;
 if(s->config_revision.present){
  const struct wr_iot_request *a=&s->provisioning.profile,*b=&s->origin.desired;
  if(a->enabled!=b->enabled)goto refused;
#define CONFIG_SAME(f) if(b->enabled&&strcmp(a->f,b->f))goto refused;
  CONFIG_SAME(ssid) CONFIG_SAME(password) CONFIG_SAME(gateway)
  CONFIG_SAME(mask) CONFIG_SAME(first) CONFIG_SAME(last)
#undef CONFIG_SAME
 }
 return 1;
 refused:(void)wr_iot_generation_config_release(&s->config_revision);
 wr_iot_saved_wipe(&s->provisioning,sizeof(s->provisioning));return 0;
}
#endif
int wr_iot_restart_generation_profile_current(const struct wr_iot_restart_generation *s)
{
 if(!s||s->owner!=getpid())return 0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!wr_iot_generation_config_owned(&s->config_revision))return 0;
 if(s->config_revision.present)return restart_config_profile_current(s);
#endif
 return generation_profile_current(&s->origin);
}

static void restart_config_wipe_terminal(struct wr_iot_restart_generation *s)
{
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 /* Generator borrow has ended before rollback/cancellation can finish. */
 (void)wr_iot_generation_config_release(&s->config_revision);
 wr_iot_saved_wipe(&s->provisioning,sizeof(s->provisioning));
#else
 (void)s;
#endif
}
int wr_iot_restart_generation_begin(struct wr_iot_restart_generation *s)
{
 if(!s||s->owner||s->busy||s->phase!=WR_RESTART_GEN_IDLE||s->profile.active||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||!wr_iot_radio_profile_guard())return 0;
 if(!wr_iot_rc_physical_resume_read(&s->origin)||!origin_valid(&s->origin)||
    !origin_current(&s->origin)||!wr_iot_restart_main_down()){
  generation_wipe(&s->origin,sizeof(s->origin));return 0;
 }
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!restart_config_take(s)){generation_wipe(&s->origin,sizeof(s->origin));return 0;}
#endif
 if(!wr_iot_radio_profile_take(&s->profile)){
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  (void)wr_iot_generation_config_release(&s->config_revision);
  wr_iot_saved_wipe(&s->provisioning,sizeof(s->provisioning));
#endif
  generation_wipe(&s->origin,sizeof(s->origin));return 0;
 }
 s->owner=getpid();s->phase=WR_RESTART_GEN_CAPTURED;
 if(!origin_current(&s->origin)||!wr_iot_restart_main_down()||wr_iot_rc_shutdown.pending){
  /* Read-only capture: cancellation cannot restore/overwrite the file. */
  (void)wr_iot_restart_profile_receipt_cancel_take(&s->rollback_receipt,&s->profile);
  if(wr_iot_radio_profile_cancel(&s->profile)){s->phase=WR_RESTART_GEN_ROLLED_BACK;restart_config_wipe_terminal(s);generation_wipe(&s->origin.desired,sizeof(s->origin.desired));}
  else s->phase=WR_RESTART_GEN_RECOVERING;
  return 0;
 }
 return 1;
}
int wr_iot_restart_generation_abort(struct wr_iot_restart_generation *s)
{
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||!s->profile.active||
    s->phase<WR_RESTART_GEN_CAPTURED||s->phase>WR_RESTART_GEN_RECOVERING||
    !origin_current(&s->origin)||!wr_iot_restart_main_down())return 0;
 s->phase=WR_RESTART_GEN_RECOVERING;return 1;
}
static int generation_step(struct wr_iot_restart_generation *s)
{
 if(s->main_may_have_started||!s->profile.active||!origin_current(&s->origin)||!wr_iot_restart_main_down())return 0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!wr_iot_generation_config_owned(&s->config_revision))return 0;
 if(s->phase>=WR_RESTART_GEN_CAPTURED&&s->phase<=WR_RESTART_GEN_VERIFIED&&
    !wr_iot_generation_config_current(&s->config_revision,s->config_revision.id,s->config_revision.created))
  s->phase=WR_RESTART_GEN_RECOVERING;
#endif
 if(s->phase==WR_RESTART_GEN_CAPTURED){
  if(wr_iot_rc_shutdown.pending){s->phase=WR_RESTART_GEN_RECOVERING;return 0;}
  if(!s->origin.intent.reload){s->phase=WR_RESTART_GEN_GENERATED;return 0;}
  s->phase=WR_RESTART_GEN_UNCERTAIN;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
  if(!wr_iot_generation_profile_enter(&s->config_revision)){s->phase=WR_RESTART_GEN_RECOVERING;return 0;}
  {
   int generated=wr_iot_radio_profile_generate(&s->profile,s->origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?generation_disabled:wr_iot_rc_restart_generate);
   int released=wr_iot_generation_profile_leave(&s->config_revision);
   s->phase=generated&&released?WR_RESTART_GEN_GENERATED:WR_RESTART_GEN_RECOVERING;
  }
#else
  if(wr_iot_radio_profile_generate(&s->profile,s->origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?generation_disabled:wr_iot_rc_restart_generate))
   s->phase=WR_RESTART_GEN_GENERATED;
  else s->phase=WR_RESTART_GEN_RECOVERING;
#endif
  return 0;
 }
 if(s->phase==WR_RESTART_GEN_GENERATED||s->phase==WR_RESTART_GEN_VERIFIED){
  if(!wr_iot_rc_shutdown.pending&&
     wr_iot_generated_matches(&s->profile.files.generated[0],s->profile.files.paths[0])&&
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
     wr_iot_generation_config_current(&s->config_revision,s->config_revision.id,s->config_revision.created)&&
     (s->config_revision.present?restart_config_profile_current(s):generation_profile_current(&s->origin))&&
#else
     generation_profile_current(&s->origin)&&
#endif
     origin_current(&s->origin)&&wr_iot_restart_main_down()){
   s->phase=WR_RESTART_GEN_VERIFIED;return 1;
  }
  s->phase=WR_RESTART_GEN_RECOVERING;return 0;
 }
 if(s->phase==WR_RESTART_GEN_UNCERTAIN){s->phase=WR_RESTART_GEN_RECOVERING;return 0;}
 if(s->phase==WR_RESTART_GEN_RECOVERING){
  if(wr_iot_radio_profile_restore(&s->profile))s->phase=WR_RESTART_GEN_RESTORED;
  return 0;
 }
 if(s->phase==WR_RESTART_GEN_RESTORED){
  if(!s->rollback_receipt.valid&&
     !wr_iot_restart_profile_receipt_take(&s->rollback_receipt,&s->profile))return 0;
  if(!wr_iot_restart_profile_receipt_current(&s->rollback_receipt))return 0;
  if(wr_iot_radio_profile_finish(&s->profile)){
   s->phase=WR_RESTART_GEN_ROLLED_BACK;restart_config_wipe_terminal(s);generation_wipe(&s->origin.desired,sizeof(s->origin.desired));
  }
 }
 return 0;
}
int wr_iot_restart_generation_step(struct wr_iot_restart_generation *s)
{
 int ok;
 if(!s||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active)return 0;
 s->busy=1;ok=generation_step(s);s->busy=0;return ok;
}

int wr_iot_restart_generation_origin_current(const struct wr_iot_restart_generation *s)
{
 return s&&s->owner==getpid()&&!s->busy&&s->profile.active&&origin_current(&s->origin);
}

int wr_iot_restart_generation_rollback_current(const struct wr_iot_restart_generation *s)
{
 struct wr_iot_rc_physical_resume current={0};int ok=0;
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||
    s->phase!=WR_RESTART_GEN_ROLLED_BACK||s->profile.active||s->profile.files.count||
    !wr_iot_rc_shutdown.active||!wr_iot_restart_main_down()||
    !wr_iot_restart_profile_receipt_current(&s->rollback_receipt))return 0;
 if(!wr_iot_rc_physical_resume_read(&current)||!origin_valid(&current)||
    s->origin.intent.restart!=current.intent.restart||s->origin.intent.radio_on!=current.intent.radio_on||
    s->origin.intent.reload!=current.intent.reload||
    !physical_origin_equal(&s->origin,&current))goto done;
 if(wr_iot_restart_main_down()&&wr_iot_restart_profile_receipt_current(&s->rollback_receipt))ok=1;
 done:generation_wipe(&current,sizeof(current));return ok;
}
