/* Compose in the one RC backend translation unit after its private owners. */
#include "profile-history.h"
#include "restart-profile.h"
static struct {
 struct wr_iot_profile_binding binding;
 struct wr_iot_restart_profile_receipt profile;
} wr_iot_rc_profile_history;
static int profile_history_equal(const struct wr_iot_profile_binding *a,
 const struct wr_iot_profile_binding *b)
{
 return a&&b&&a->kind!=WR_PROFILE_BACKEND_NONE&&a->kind==b->kind&&
  a->created&&a->created==b->created&&
  memchr(a->id,0,sizeof(a->id))&&memchr(b->id,0,sizeof(b->id))&&
  wr_iot_control_id(a->id)&&!strcmp(a->id,b->id)&&
  a->identity.adapter_epoch&&a->identity.device_generation&&
  a->identity.adapter_epoch==b->identity.adapter_epoch&&
  a->identity.device_generation==b->identity.device_generation;
}
static int profile_history_backend(struct wr_iot_profile_binding *out)
{
 struct wr_iot_profile_binding b={0};struct wr_iot_control_result r={0};
 if(!out||!wr_iot_radio_profile_guard())return 0;
 if(rebind.owner){
  if(rebind.owner!=getpid()||rebind.busy||rebind.phase!=WR_REBIND_OWNER_ACTIVE)return 0;
  b.kind=WR_PROFILE_BACKEND_REBIND_ACTIVE;
  memcpy(b.id,rebind.start.input.id,sizeof(b.id));b.created=rebind.start.input.created;
  b.identity=rebind.start.start.identity;
 }else{
  if(backend.owner!=getpid()||backend.busy)return 0;
  if(backend.phase==WR_IOT_OWNER_ACTIVE){
   b.kind=WR_PROFILE_BACKEND_ACTIVE;
   memcpy(b.id,backend.start.input.id,sizeof(b.id));b.created=backend.start.input.created;
   b.identity=backend.start.open.attempt.identity;
  }else if(backend.phase==WR_IOT_OWNER_INITIAL_OFF){
   b.kind=WR_PROFILE_BACKEND_INITIAL_OFF;
   memcpy(b.id,backend.initial_off.id,sizeof(b.id));b.created=backend.initial_off.created;
   b.identity.adapter_epoch=backend.initial_off.idle.epoch;
   b.identity.device_generation=backend.initial_off.idle.generation;
  }else return 0;
 }
 if(!profile_history_equal(&b,&b))return 0;
 memcpy(r.id,b.id,sizeof(r.id));r.created=b.created;r.state=WR_IOT_RESULT_APPLIED;
 if(rebind.owner?!wr_iot_rebind_owner_observed(&rebind,&r):
                  !wr_iot_activation_owner_observed(&backend,&r))return 0;
 *out=b;return 1;
}
/* Only after complete caller preflight; nonfallible inert metadata transfer. */
static void profile_history_commit(const struct wr_iot_profile_binding *binding,
 const struct wr_iot_restart_profile_receipt *profile)
{wr_iot_rc_profile_history.binding=*binding;wr_iot_rc_profile_history.profile=*profile;}
int wr_iot_rc_profile_history_remember(const struct wr_iot_profile_binding *expected,
 const struct wr_iot_restart_profile_receipt *profile)
{
 struct wr_iot_profile_binding before={0},after={0};
 if(!profile||profile->file.existed!=1||profile->file.metadata.st_size<=0||
    !profile_history_backend(&before)||!profile_history_equal(expected,&before)||
    !wr_iot_restart_profile_receipt_current(profile)||!profile_history_backend(&after)||
    !profile_history_equal(&before,&after)||!wr_iot_restart_profile_receipt_current(profile))return 0;
 profile_history_commit(&before,profile);return 1;
}
int wr_iot_rc_profile_history_read(struct wr_iot_profile_binding *binding,
 struct wr_iot_restart_profile_receipt *profile)
{
 struct wr_iot_profile_binding before={0},after={0};
 if(!binding||!profile)return 0;
 memset(binding,0,sizeof(*binding));memset(profile,0,sizeof(*profile));
 if(wr_iot_rc_profile_history.profile.file.existed!=1||wr_iot_rc_profile_history.profile.file.metadata.st_size<=0||
    !profile_history_backend(&before)||
    !profile_history_equal(&before,&wr_iot_rc_profile_history.binding)||
    !wr_iot_restart_profile_receipt_current(&wr_iot_rc_profile_history.profile)||
    !profile_history_backend(&after)||!profile_history_equal(&before,&after)||
    !wr_iot_restart_profile_receipt_current(&wr_iot_rc_profile_history.profile))return 0;
 *binding=before;*profile=wr_iot_rc_profile_history.profile;return 1;
}
/* Ordinary mailbox ON has no generation owner to donate a receipt. Bootstrap
 * only from its retained ACTIVE request plus the actual fixed-path scanner and
 * independent existing driver/network observer. Saved desired keys never enter
 * this comparison. Failure leaves history absent/stale, so reload0 refuses. */
int wr_iot_rc_profile_history_active(void)
{
 struct wr_iot_profile_binding before={0},after={0};struct wr_iot_restart_profile_receipt file={0};
 const struct wr_iot_request *request;size_t length;
 if(!profile_history_backend(&before)||
    (before.kind!=WR_PROFILE_BACKEND_ACTIVE&&before.kind!=WR_PROFILE_BACKEND_REBIND_ACTIVE))return 0;
 request=before.kind==WR_PROFILE_BACKEND_ACTIVE?&backend.start.input.request:&rebind.start.input.request;
 length=strlen(WR_IOT_RADIO_PROFILE_PATH);if(!length||length>=sizeof(file.path))return 0;
 memcpy(file.path,WR_IOT_RADIO_PROFILE_PATH,length+1);file.owner=getpid();file.valid=1;
 if(!wr_iot_generated_capture(&file.file,file.path)||file.file.existed!=1||file.file.metadata.st_size<=0||
    !wr_iot_restart_profile_file_current(request)||!wr_iot_restart_profile_receipt_current(&file)||
    !profile_history_backend(&after)||!profile_history_equal(&before,&after)||
    !wr_iot_restart_profile_file_current(request)||!wr_iot_restart_profile_receipt_current(&file))return 0;
 profile_history_commit(&before,&file);return 1;
}
