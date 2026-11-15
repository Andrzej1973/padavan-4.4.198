#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-disabled.h"
#include "rc-shutdown-admission.h"
#include "restart-guest-policy.h"
#include "restart-guest-isolation.h"
static int disabled_parent(struct wr_iot_on_restore *r)
{
 return r&&r->owner==getpid()&&!r->busy&&r->phase==WR_ON_RESTORE_PREPARED&&
  r->generation.desired.enabled==0&&r->generation.admission&&
  r->generation.owner==getpid()&&r->generation.main_may_have_started&&
  r->main.generation==&r->generation&&r->guest.main==&r->main&&
  r->services.guest==&r->guest&&r->multicast.main==&r->main&&
  r->multicast.guest==&r->guest&&!r->handoff_created&&
  !r->terminal.owner&&!r->child.owner&&!r->child.attempted&&
  wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&
  wr_iot_on_restore_step(r)==1;
}
int wr_iot_on_disabled_current(struct wr_iot_on_disabled *s)
{
 int ok;
 if(!s||s->owner!=getpid()||s->busy||!disabled_parent(s->restore))return 0;
 s->busy=1;
 ok=wr_iot_initial_off_restarted_observed(&s->idle,
  &s->restore->generation.admission->released,&s->restore->main.identity)&&
  disabled_parent(s->restore);
 s->busy=0;return ok;
}
int wr_iot_on_disabled_begin(struct wr_iot_on_disabled *s,struct wr_iot_on_restore *r,
 const struct wr_iot_control_request *request)
{
 if(!s||!request||s->owner||s->busy||s->restore||s->idle.owner||
    request->request.enabled!=0||!r||r->wan.owner||!disabled_parent(r))return 0;
 s->busy=1;
 if(!wr_iot_initial_off_begin(&s->idle,request)){s->busy=0;return 0;}
 /* Retain the captured identity even if the next observation refuses. */
 s->owner=getpid();s->restore=r;
 s->busy=0;return wr_iot_on_disabled_current(s);
}

int wr_iot_on_disabled_release_current(struct wr_iot_on_disabled *s)
{
 struct wr_iot_restart_service_policy policy;struct wr_iot_on_restore *r;
 struct wr_iot_on_admission *a;struct wr_iot_radio_profile_state *p;
 int desired,isolate;
 if(!wr_iot_on_disabled_current(s))return 0;
 r=s->restore;a=r->generation.admission;p=&a->profile;
 if(a->owner!=getpid()||a->busy!=1||a->guard!=1||
    a->phase!=WR_ON_ADMISSION_CAPTURED||a->fence.owner!=getpid()||a->fence.level!=1||
    !wr_iot_rc_shutdown.radio_off_owned||!wr_iot_radio_profile_owned(p)||
    p->recovering||p->recovered||p->removing||p->files.count!=1||
    p->files.pending||p->files.restored||
    (r->generation.reload&&(!p->generated||!p->files.sealed))||
    (!r->generation.reload&&(p->generated||p->files.journalled))||
    r->wan.owner!=getpid()||r->wan.radio_on!=1||r->wan.attempted||r->wan.returned||
    r->wan.plan<WR_WAN_NONE||r->wan.plan>WR_WAN_RECONNECT||
    !wr_iot_rc_restart_guest_policy(&desired)||desired!=r->guest.desired||
    !wr_iot_rc_restart_guest_isolation_policy(&isolate)||isolate!=r->guest.isolate||
    !wr_iot_rc_restart_service_policy(&policy)||policy.enterprise!=r->services.policy.enterprise||
    policy.kick_rssi!=r->services.policy.kick_rssi||policy.assoc_rssi!=r->services.policy.assoc_rssi||
    !wr_iot_rc_restart_auth_process_current(&policy)||
    !wr_iot_rc_restart_wan_current(1,r->wan.plan)||
    !wr_iot_generated_matches(&p->files.generated[0],p->files.paths[0]))return 0;
 return wr_iot_on_disabled_current(s);
}
