#define _GNU_SOURCE
#include <unistd.h>
#include "radio-on-prehandoff.h"
#include "restart-profile.h"
#include "rc-shutdown-admission.h"
int wr_iot_on_prehandoff_cancel_current(struct wr_iot_on_restore *s)
{
 struct wr_iot_driver_identity current={0};int guest;
 if(!s||s->owner!=getpid()||s->busy||s->handoff_created||
    s->phase<WR_ON_RESTORE_MAIN_WAIT||s->phase>WR_ON_RESTORE_PREPARED||
    s->main.owner!=getpid()||s->main.busy||s->main.generation!=&s->generation||
    (s->main.phase!=WR_ON_MAIN_WAIT&&s->main.phase!=WR_ON_MAIN_READY)||
    s->guest.busy||s->services.busy||s->multicast.busy||s->wan.owner||
    s->terminal.owner||s->terminal.child||s->terminal.guard||s->terminal.fence.owner||
    s->child.owner||s->child.attempted||
    !s->generation.admission||!s->generation.main_may_have_started||s->generation.phase!=WR_ON_GEN_VERIFIED||
    !s->generation.admission->profile.active||s->generation.admission->profile.files.count!=1||
    s->generation.admission->profile.files.pending||
    s->generation.admission->profile.recovering||s->generation.admission->profile.recovered||
    s->generation.admission->profile.removing||s->generation.admission->profile.files.restored||
    (s->generation.reload&&(!s->generation.admission->profile.generated||!s->generation.admission->profile.files.sealed))||
    (!s->generation.reload&&(s->generation.admission->profile.generated||s->generation.admission->profile.files.journalled))||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_on_generation_origin_current(&s->generation))return 0;
 if(s->guest.owner&&(s->guest.owner!=getpid()||s->guest.busy||s->guest.main!=&s->main||
    (s->guest.phase!=WR_ON_GUEST_DOWN_OBSERVED&&s->guest.phase!=WR_ON_GUEST_POLICY_OFF)))return 0;
 if(!wr_iot_restart_guest_admin_state(&guest)||guest||
    !wr_iot_generated_matches(&s->generation.admission->profile.files.generated[0],s->generation.admission->profile.files.paths[0])||
    !wr_iot_restart_profile_current(&s->generation.desired)||
    !wr_iot_rebind_configuration_current(&s->generation.admission->released,s->open_id,&current)||
    current.adapter_epoch<=s->generation.admission->released.epoch||
    current.device_generation!=s->generation.admission->released.generation||
    (s->main.identity.adapter_epoch&&
     (s->main.identity.adapter_epoch!=current.adapter_epoch||s->main.identity.device_generation!=current.device_generation)))return 0;
 return wr_iot_restart_guest_admin_state(&guest)&&!guest&&
  wr_iot_generated_matches(&s->generation.admission->profile.files.generated[0],s->generation.admission->profile.files.paths[0])&&
  wr_iot_on_generation_origin_current(&s->generation);
}
