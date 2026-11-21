#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-release.h"
#include "rc-shutdown-admission.h"
static int cold_release_profile_take(struct wr_iot_cold_release *s)
{
 struct wr_iot_restart_profile_receipt receipt={0};struct wr_iot_radio_profile_state *p;
 size_t n;
 if(!s->handoff||!s->handoff->parent)return 0;
 if(s->profile.valid)return wr_iot_restart_profile_receipt_current(&s->profile);
 p=&s->handoff->parent->admission.profile;
 if(!wr_iot_radio_profile_owned(p)||p->files.count!=1||p->recovering||p->recovered||
    p->removing||p->files.pending||p->files.restored||
    !memchr(p->files.paths[0],0,sizeof(p->files.paths[0])))return 0;
 n=strlen(p->files.paths[0]);if(!n||n>=sizeof(receipt.path))return 0;
 memcpy(receipt.path,p->files.paths[0],n+1);receipt.file=p->files.generated[0];
 receipt.owner=getpid();receipt.valid=1;
 if(!wr_iot_restart_profile_receipt_current(&receipt))return 0;
 s->profile=receipt;return 1;
}
static int cold_release_binding_current(const struct wr_iot_cold_release *s)
{
 return s->handoff&&s->parent&&s->handoff->parent==s->parent&&
  s->created&&s->created==s->handoff->created&&
  memchr(s->id,0,sizeof(s->id))&&memchr(s->handoff->id,0,sizeof(s->handoff->id))&&
  wr_iot_control_id(s->id)&&!strcmp(s->id,s->handoff->id)&&
  s->identity.adapter_epoch&&s->identity.device_generation&&
  s->identity.adapter_epoch==s->handoff->identity.adapter_epoch&&
  s->identity.device_generation==s->handoff->identity.device_generation;
}
int wr_iot_cold_release_current(struct wr_iot_cold_release *s)
{
 if(!s||s->owner!=getpid()||s->busy||!cold_release_binding_current(s)||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_cold_handoff_current(s->handoff))return 0;
 s->busy=1;
 if(!wr_iot_cold_policy_current(&s->policy)||!cold_release_profile_take(s))goto refused;
 if(!s->wan.owner&&!wr_iot_wan_followup_capture(&s->wan,1))goto refused;
 if(s->wan.owner!=getpid()||s->wan.radio_on!=1||s->wan.attempted||s->wan.returned||
    s->wan.plan<WR_WAN_NONE||s->wan.plan>WR_WAN_RECONNECT||
    !wr_iot_rc_restart_wan_current(1,s->wan.plan)||
    !wr_iot_restart_profile_receipt_current(&s->profile)||
    !wr_iot_cold_handoff_current(s->handoff)||!cold_release_binding_current(s)||!wr_iot_cold_policy_current(&s->policy))goto refused;
 s->busy=0;return 1;
 refused:s->busy=0;return 0;
}
int wr_iot_cold_release_begin(struct wr_iot_cold_release *s,struct wr_iot_cold_handoff *handoff)
{
 if(!s||!handoff||s->owner||s->busy||s->handoff||s->parent||s->created||s->profile.valid||s->profile.owner||s->policy.owner||s->wan.owner||
    !wr_iot_cold_handoff_current(handoff))return 0;
 s->policy.owner=getpid();s->policy.guest=handoff->parent->guest.desired;
 s->policy.isolate=handoff->parent->guest.isolate;s->policy.services=handoff->parent->services.policy;
 s->policy.multicast=handoff->parent->multicast.policy;
 s->owner=getpid();s->handoff=handoff;s->parent=handoff->parent;s->identity=handoff->identity;
 memcpy(s->id,handoff->id,sizeof(s->id));s->created=handoff->created;
 (void)wr_iot_cold_release_current(s);
 return 1;
}
