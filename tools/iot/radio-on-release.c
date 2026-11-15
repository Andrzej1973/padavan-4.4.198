#define _GNU_SOURCE
#include <unistd.h>
#include "radio-on-release.h"
#include "restart-main-bridge.h"
#include "restart-guest-policy.h"
#include "restart-guest-bridge.h"
#include "restart-guest-isolation.h"
#include "rc-shutdown-admission.h"
int wr_iot_on_release_current(struct wr_iot_on_restore *s)
{
 struct wr_iot_restart_service_policy policy;struct wr_iot_radio_profile_state *p;
 struct wr_iot_on_admission *a;int desired,isolate,state;
 if(!s||s->terminal.owner||s->terminal.busy||s->child.owner||s->child.attempted||
    !wr_iot_on_rebind_current(s)||!s->generation.main_may_have_started||
    s->generation.phase!=WR_ON_GEN_VERIFIED||!s->generation.admission)return 0;
 a=s->generation.admission;p=&a->profile;
 if(a->owner!=getpid()||a->busy!=1||a->guard!=1||a->phase!=WR_ON_ADMISSION_CAPTURED||
    a->fence.owner!=getpid()||a->fence.level!=1||!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_rc_shutdown.radio_off_owned||!wr_iot_radio_profile_owned(p)||p->recovering||p->recovered||p->removing||
    p->files.count!=1||p->files.pending||p->files.restored||
    (s->generation.reload&&(!p->generated||!p->files.sealed))||
    (!s->generation.reload&&(p->generated||p->files.journalled))||
    s->guest.busy||s->guest.phase!=(s->guest.desired?WR_ON_GUEST_ADMIN_UP:WR_ON_GUEST_POLICY_OFF)||
    (s->guest.desired!=0&&s->guest.desired!=1)||s->services.busy||
    s->services.phase!=WR_ON_SERVICES_SUBMITTED||s->services.next!=3||s->services.attempted!=7||
    s->wan.owner!=getpid()||s->wan.radio_on!=1||s->wan.attempted||s->wan.returned||
    s->wan.plan<WR_WAN_NONE||s->wan.plan>WR_WAN_RECONNECT)return 0;
 if(!wr_iot_generated_matches(&p->files.generated[0],p->files.paths[0])||
    !wr_iot_restart_profile_current(&s->generation.desired)||!wr_iot_restart_main_bridge_current()||
    !wr_iot_rc_restart_guest_policy(&desired)||desired!=s->guest.desired||
    !wr_iot_rc_restart_guest_isolation_policy(&isolate)||isolate!=s->guest.isolate||
    !wr_iot_restart_guest_admin_state(&state)||state!=desired||
    (desired&&(!wr_iot_restart_guest_bridge_current()||!wr_iot_restart_guest_isolation_current(isolate)))||
    !wr_iot_rc_restart_service_policy(&policy)||policy.enterprise!=s->services.policy.enterprise||
    policy.kick_rssi!=s->services.policy.kick_rssi||policy.assoc_rssi!=s->services.policy.assoc_rssi||
    !wr_iot_rc_restart_auth_process_current(&policy)||
    !wr_iot_rc_restart_wan_current(1,s->wan.plan)||wr_iot_rc_shutdown.pending)return 0;
 return wr_iot_generated_matches(&p->files.generated[0],p->files.paths[0])&&wr_iot_on_rebind_current(s);
}
