#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-handoff.h"
#include "rc-cold-start.h"
#include "radio-on-aux.h"
#include "restart-main-bridge.h"
#include "restart-guest-policy.h"
#include "restart-guest-bridge.h"
#include "restart-guest-isolation.h"
#include "rc-shutdown-admission.h"
static void cold_handoff_wipe(void*p,size_t n)
{volatile unsigned char*b=p;while(n--)*b++=0;}
static int cold_handoff_parent_current(struct wr_iot_cold_owner *s)
{
 struct wr_iot_cold_admission *a;struct wr_iot_radio_profile_state *p;
 struct wr_iot_restart_service_policy policy;int desired,isolate,state;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_COLD_OWNER_PREPARED||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||!wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||
    s->generation.owner!=getpid()||s->generation.busy||!s->generation.main_may_have_started||
    s->generation.phase!=WR_COLD_GEN_VERIFIED||s->generation.desired.enabled!=1||
    s->generation.admission!=&s->admission||s->main.generation!=&s->generation||
    s->guest.main!=&s->main||s->services.guest!=&s->guest||
    s->multicast.main!=&s->main||s->multicast.guest!=&s->guest)return 0;
 a=&s->admission;p=&a->profile;
 if(a->owner!=getpid()||a->busy!=1||a->guard!=1||a->phase!=WR_COLD_CAPTURED||
    a->fence.owner!=getpid()||a->fence.level!=1||!wr_iot_radio_profile_owned(p)||
    p->recovering||p->recovered||p->removing||p->files.count!=1||p->files.pending||p->files.restored||
    (s->reload&&(!p->generated||!p->files.sealed))||(!s->reload&&(p->generated||p->files.journalled))||
    s->guest.owner!=getpid()||s->guest.busy||
    s->guest.phase!=(s->guest.desired?WR_COLD_GUEST_ADMIN_UP:WR_COLD_GUEST_POLICY_OFF)||
    s->services.owner!=getpid()||s->services.busy||s->services.phase!=WR_COLD_SERVICES_SUBMITTED||
    s->services.next!=3||s->services.attempted!=7)return 0;
 return wr_iot_generated_matches(&p->files.generated[0],p->files.paths[0])&&
  wr_iot_cold_generation_profile_current(&s->generation)&&wr_iot_restart_main_bridge_current()&&
  wr_iot_rc_restart_guest_policy(&desired)&&desired==s->guest.desired&&
  wr_iot_rc_restart_guest_isolation_policy(&isolate)&&isolate==s->guest.isolate&&
  wr_iot_restart_guest_admin_state(&state)&&state==desired&&
  (!desired||(wr_iot_restart_guest_bridge_current()&&wr_iot_restart_guest_isolation_current(isolate)))&&
  wr_iot_rc_restart_service_policy(&policy)&&policy.enterprise==s->services.policy.enterprise&&
  policy.kick_rssi==s->services.policy.kick_rssi&&policy.assoc_rssi==s->services.policy.assoc_rssi&&
  wr_iot_rc_restart_auth_process_current(&policy)&&wr_iot_cold_multicast_observed(&s->multicast)&&
  wr_iot_on_aux_down_current()&&!wr_iot_rc_shutdown.pending;
}
int wr_iot_cold_handoff_begin(struct wr_iot_cold_handoff *s,struct wr_iot_cold_owner *parent)
{
 struct wr_iot_control_request request={0};
 if(!s||!parent||s->owner||s->busy||s->attempted||s->parent||s->phase!=WR_COLD_HANDOFF_IDLE||
    !wr_iot_cold_owner_step(parent)||!cold_handoff_parent_current(parent))return 0;
 s->owner=getpid();s->busy=1;s->attempted=1;s->parent=parent;s->identity=parent->main.identity;
 memcpy(s->id,parent->input.id,sizeof(s->id));s->created=parent->input.created;
 s->phase=WR_COLD_HANDOFF_RETAINED;
 request=parent->input;request.request=parent->generation.desired;
 s->backend_claimed=wr_iot_rc_cold_start_begin(parent,&request);
 if(s->backend_claimed)s->phase=WR_COLD_HANDOFF_WAIT;
 cold_handoff_wipe(&request,sizeof(request));s->busy=0;return 1;
}
static int cold_handoff_observe(struct wr_iot_cold_handoff *s,int advance)
{
 struct wr_iot_control_request request={0};int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!s->attempted||!s->backend_claimed||!s->parent||
    (s->phase!=WR_COLD_HANDOFF_WAIT&&s->phase!=WR_COLD_HANDOFF_ACTIVE)||
    !s->created||!memchr(s->id,0,sizeof(s->id))||!wr_iot_control_id(s->id)||
    strcmp(s->id,s->parent->input.id)||s->created!=s->parent->input.created||
    s->identity.adapter_epoch!=s->parent->main.identity.adapter_epoch||
    s->identity.device_generation!=s->parent->main.identity.device_generation||
    !cold_handoff_parent_current(s->parent))return 0;
 s->busy=1;memcpy(request.id,s->id,sizeof(request.id));request.created=s->created;
 request.request=s->parent->generation.desired;
 if(advance)(void)wr_iot_rc_cold_start_progress(s->parent,&request);
 if(wr_iot_rc_cold_active_current(s->parent,&request)&&cold_handoff_parent_current(s->parent)){
  s->phase=WR_COLD_HANDOFF_ACTIVE;ok=1;
 }
 cold_handoff_wipe(&request,sizeof(request));s->busy=0;return ok;
}
int wr_iot_cold_handoff_step(struct wr_iot_cold_handoff *s)
{return cold_handoff_observe(s,1);}
int wr_iot_cold_handoff_current(struct wr_iot_cold_handoff *s)
{return cold_handoff_observe(s,0);}
