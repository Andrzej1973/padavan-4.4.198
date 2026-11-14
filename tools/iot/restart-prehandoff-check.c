#define _GNU_SOURCE
#include <unistd.h>
#include "restart-restore.h"
#include "restart-profile.h"
#include "rc-shutdown-admission.h"
int wr_iot_restart_prehandoff_cancel_check(struct wr_iot_restart_restore *s)
{
 struct wr_iot_driver_identity current={0};int guest;
 if(!s||s->owner!=getpid()||s->busy||s->handoff_created||
    s->phase<WR_RESTORE_MAIN_WAIT||s->phase>WR_RESTORE_PREPARED||
    s->main.owner!=getpid()||s->main.busy||s->main.generation!=&s->generation||
    s->main.phase==WR_MAIN_NOT_SUBMITTED||
    !s->generation.main_may_have_started||s->generation.phase!=WR_RESTART_GEN_VERIFIED||
    !s->generation.profile.active||s->generation.profile.files.count!=1||
    s->generation.profile.files.pending||!wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_restart_generation_origin_current(&s->generation))return 0;
 if(s->guest.owner&&(s->guest.owner!=getpid()||s->guest.busy||s->guest.main!=&s->main||
    (s->guest.phase!=WR_GUEST_DOWN_OBSERVED&&s->guest.phase!=WR_GUEST_POLICY_OFF)))return 0;
 if(!wr_iot_restart_guest_admin_state(&guest)||guest||
    !wr_iot_generated_matches(&s->generation.profile.files.generated[0],s->generation.profile.files.paths[0])||
    !wr_iot_restart_profile_current(&s->generation.origin.desired)||
    !wr_iot_rebind_configuration_current(&s->generation.origin.physical,s->open_id,&current)||
    current.adapter_epoch<=s->generation.origin.physical.epoch||
    current.device_generation!=s->generation.origin.physical.generation||
    (s->main.identity.adapter_epoch&&
     (s->main.identity.adapter_epoch!=current.adapter_epoch||s->main.identity.device_generation!=current.device_generation)))return 0;
 return wr_iot_restart_guest_admin_state(&guest)&&!guest&&
  wr_iot_generated_matches(&s->generation.profile.files.generated[0],s->generation.profile.files.paths[0])&&
  wr_iot_restart_generation_origin_current(&s->generation);
}
