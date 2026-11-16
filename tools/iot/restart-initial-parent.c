#define _GNU_SOURCE
#include <unistd.h>
#include "restart-initial-parent.h"
#include "restart-profile.h"
#include "restart-main-bridge.h"
#include "restart-guest-policy.h"
#include "restart-guest-bridge.h"
#include "restart-guest-isolation.h"
#include "rc-shutdown-admission.h"
int wr_iot_restart_initial_parent_current(struct wr_iot_restart_restore *s,int before_start)
{
 struct wr_iot_restart_service_policy policy;int desired,isolate,state;
 if((before_start!=0&&before_start!=1)||!s||s->owner!=getpid()||s->busy!=1||
    s->phase!=WR_RESTORE_HANDOFF||!s->handoff_created||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    s->generation.owner!=getpid()||s->generation.busy||
    s->generation.phase!=WR_RESTART_GEN_VERIFIED||!s->generation.main_may_have_started||
    !s->generation.profile.active||s->generation.profile.files.count!=1||
    s->generation.profile.files.pending||s->generation.profile.recovering||s->generation.profile.removing||
    s->main.owner!=getpid()||s->main.busy||s->main.phase!=WR_MAIN_READY||
    s->main.generation!=&s->generation||s->main.bridge_attempted!=1||
    !s->main.identity.adapter_epoch||!s->main.identity.device_generation||
    s->main.identity.adapter_epoch<=s->generation.origin.initial.epoch||
    s->main.identity.device_generation!=s->generation.origin.initial.generation||
    !wr_iot_iapp_child_closed(&s->iapp)||(s->iapp.attempted&&s->iapp.result!=1)||
    s->multicast.main!=&s->main||s->multicast.guest!=&s->guest||
    s->guest.owner!=getpid()||s->guest.busy||s->guest.main!=&s->main||
    (s->guest.desired!=0&&s->guest.desired!=1)||
    s->guest.phase!=(s->guest.desired?WR_GUEST_ADMIN_UP:WR_GUEST_POLICY_OFF)||
    s->services.owner!=getpid()||s->services.busy||s->services.main!=&s->main||
    s->services.phase!=WR_SERVICES_SUBMITTED||s->services.next!=3||s->services.attempted!=7||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 if(!wr_iot_restart_generation_origin_current(&s->generation)||
    !wr_iot_generated_matches(&s->generation.profile.files.generated[0],s->generation.profile.files.paths[0])||
    !wr_iot_restart_initial_enabled_profile_current(&s->generation.origin.desired)||
    !wr_iot_restart_main_bridge_current()||
    !wr_iot_rc_restart_guest_policy(&desired)||desired!=s->guest.desired||
    !wr_iot_rc_restart_guest_isolation_policy(&isolate)||isolate!=s->guest.isolate||
    !wr_iot_restart_guest_admin_state(&state)||state!=desired||
    (desired&&(!wr_iot_restart_guest_bridge_current()||!wr_iot_restart_guest_isolation_current(isolate)))||
    !wr_iot_rc_restart_service_policy(&policy)||policy.enterprise!=s->services.policy.enterprise||
    policy.kick_rssi!=s->services.policy.kick_rssi||policy.assoc_rssi!=s->services.policy.assoc_rssi||
    !wr_iot_rc_restart_auth_process_current(&policy)||
    !wr_iot_restart_multicast_observed(&s->multicast))return 0;
 if(before_start&&!wr_iot_restart_main_lan_step(&s->main))return 0;
 return wr_iot_restart_generation_origin_current(&s->generation)&&!wr_iot_rc_shutdown.pending;
}
