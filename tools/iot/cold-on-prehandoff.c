#define _GNU_SOURCE
#include <unistd.h>
#include "cold-on-prehandoff.h"
#include "restart-guest-up.h"
#include "rc-shutdown-admission.h"
int wr_iot_cold_prehandoff_shutdown_current(struct wr_iot_cold_owner *p)
{
 struct wr_iot_cold_admission *a;struct wr_iot_radio_profile_state *profile;
 struct wr_iot_idle_result before={0},after={0};int guest;
 if(!p||p->owner!=getpid()||p->busy||p->phase<WR_COLD_OWNER_MAIN_WAIT||p->phase>WR_COLD_OWNER_PREPARED||
    p->main.owner!=getpid()||p->main.busy||p->main.generation!=&p->generation||
    (p->main.phase!=WR_COLD_MAIN_WAIT&&p->main.phase!=WR_COLD_MAIN_READY)||
    p->generation.owner!=getpid()||p->generation.busy||p->generation.admission!=&p->admission||
    !p->generation.main_may_have_started||p->generation.phase!=WR_COLD_GEN_VERIFIED||
    p->guest.busy||p->services.busy||p->multicast.busy||!wr_iot_rc_shutdown.active||
    !wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    ))return 0;
 a=&p->admission;profile=&a->profile;
 if(a->owner!=getpid()||a->guard!=1||a->busy!=1||a->phase!=WR_COLD_CAPTURED||
    a->fence.owner!=getpid()||a->fence.level!=1||!wr_iot_radio_profile_owned(profile)||
    profile->files.count!=1||profile->files.pending||profile->files.restored||profile->recovering||
    profile->recovered||profile->removing||
    (p->reload&&(!profile->generated||!profile->files.sealed))||
    (!p->reload&&(profile->generated||profile->files.journalled)))return 0;
 if((p->guest.owner&&(p->guest.owner!=getpid()||p->guest.main!=&p->main||
      (p->guest.phase!=WR_COLD_GUEST_DOWN_OBSERVED&&p->guest.phase!=WR_COLD_GUEST_POLICY_OFF)))||
    (p->services.owner&&(p->services.owner!=getpid()||p->services.guest!=&p->guest))||
    (p->multicast.owner&&(p->multicast.owner!=getpid()||p->multicast.main!=&p->main||p->multicast.guest!=&p->guest)))return 0;
 if(!wr_iot_rc_cold_never_started(p)||!wr_iot_restart_guest_admin_state(&guest)||guest||
    !wr_iot_generated_matches(&profile->files.generated[0],profile->files.paths[0])||
    !wr_iot_cold_generation_profile_current(&p->generation)||
    !wr_iot_driver_initial_idle_read(a->nonce,&before)||!wr_iot_driver_initial_idle_read(a->nonce,&after)||
    !a->down.epoch||!a->down.generation||!a->down.main_close_serial||
    before.epoch<=a->down.epoch||before.generation!=a->down.generation||
    !before.serial||after.serial<=before.serial||after.epoch!=before.epoch||after.generation!=before.generation||
    (p->main.identity.adapter_epoch&&(p->main.identity.adapter_epoch!=after.epoch||
     p->main.identity.device_generation!=after.generation)))return 0;
 return wr_iot_rc_cold_never_started(p)&&wr_iot_restart_guest_admin_state(&guest)&&!guest&&
  wr_iot_generated_matches(&profile->files.generated[0],profile->files.paths[0]);
}
