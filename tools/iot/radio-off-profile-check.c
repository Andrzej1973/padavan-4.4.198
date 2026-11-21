#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-off-profile.h"
#include "restart-profile.h"
#include "precreated-profile-request.h"
#include "rc.h"
static const char *off_profile_read(void *unused,const char *key)
{(void)unused;return nvram_safe_get(key);}
static void off_profile_wipe(void *p,size_t n)
{volatile unsigned char *b=p;while(n--)*b++=0;}
int wr_iot_rc_off_profile_current(void)
{
 struct wr_iot_precreated_profile_request saved={0};
 struct wr_iot_request desired={0};int ok=0;
 if(!wr_iot_radio_profile_guard()||
    !wr_iot_precreated_profile_request_read(&saved,off_profile_read,NULL))goto done;
 /* enabled=1 selects the existing profile scanner; no request is submitted.
  * Cold third BSS remains inactive; saved runtime OFF is not rewritten. */
 desired.enabled=1;
 memcpy(desired.ssid,saved.ssid,sizeof(desired.ssid));
 memcpy(desired.password,saved.password,sizeof(desired.password));
 ok=wr_iot_restart_profile_current(&desired);
 done:off_profile_wipe(&desired,sizeof(desired));off_profile_wipe(&saved,sizeof(saved));return ok;
}

int wr_iot_off_profile_current(const struct wr_iot_off_profile *s)
{
 if(!s||s->self!=s||s->owner!=getpid()||
    (s->phase!=WR_OFF_PROFILE_GENERATED&&s->phase!=WR_OFF_PROFILE_VERIFIED)||
    !wr_iot_radio_profile_guard()||!s->baseline.active||
    s->baseline.owner!=getpid()||s->baseline.files.count!=1||
    !wr_iot_generated_matches(&s->baseline.files.generated[0],s->baseline.files.paths[0]))return 0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!s->reload)return
  (s->history_binding.kind==WR_PROFILE_BACKEND_ACTIVE||s->history_binding.kind==WR_PROFILE_BACKEND_REBIND_ACTIVE)&&
  s->history_binding.identity.adapter_epoch==s->released.epoch&&
  s->history_binding.identity.device_generation==s->released.generation&&
  wr_iot_restart_profile_receipt_current(&s->history_profile)&&
  !strcmp(s->history_profile.path,s->baseline.files.paths[0]);
 if(s->reload){
  struct wr_iot_saved_config config={0};int ok=0;
  if(!wr_iot_generation_config_owned(&s->config_revision))return 0;
  if(s->config_revision.present){
   if(wr_iot_saved_config_decode(&config,s->config_revision.record,
      strnlen(s->config_revision.record,sizeof(s->config_revision.record)))){
    config.profile.enabled=1; /* Scanner selection, including provisioned OFF. */
    ok=wr_iot_restart_profile_file_current(&config.profile);
   }
   wr_iot_saved_wipe(&config,sizeof(config));return ok;
  }
 }
#endif
 return wr_iot_rc_off_profile_current();
}
