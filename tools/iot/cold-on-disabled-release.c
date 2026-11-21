#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-disabled-release.h"
#include "rc-shutdown-admission.h"
static int cold_disabled_release_bound(struct wr_iot_cold_disabled_release *s)
{
 return s->disabled&&s->parent&&s->disabled->parent==s->parent&&s->created&&
  s->created==s->disabled->idle.created&&memchr(s->id,0,sizeof(s->id))&&
  !memcmp(s->id,s->disabled->idle.id,sizeof(s->id))&&
  s->identity.adapter_epoch==s->disabled->idle.idle.epoch&&
  s->identity.device_generation==s->disabled->idle.idle.generation&&
  wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&wr_iot_rc_shutdown.radio_off_owned&&
  !wr_iot_rc_shutdown.radio_on_owned&&wr_iot_cold_disabled_current(s->disabled)&&
  wr_iot_cold_policy_current(&s->policy);
}
int wr_iot_cold_disabled_release_current(struct wr_iot_cold_disabled_release *s)
{
 struct wr_iot_restart_profile_receipt receipt={0};struct wr_iot_radio_profile_state *p;size_t n;int ok=0;
 if(!s||s->owner!=getpid()||s->busy||!cold_disabled_release_bound(s))return 0;
 s->busy=1;p=&s->parent->admission.profile;
 if(!wr_iot_radio_profile_owned(p)||p->recovering||p->recovered||p->removing||
    p->files.count!=1||p->files.pending||p->files.restored||
    (s->parent->reload&&(!p->generated||!p->files.sealed))||
    (!s->parent->reload&&(p->generated||p->files.journalled)))goto done;
 if(!s->profile.valid){
  if(!memchr(p->files.paths[0],0,sizeof(p->files.paths[0])))goto done;
  n=strlen(p->files.paths[0]);if(!n||n>=sizeof(receipt.path))goto done;
  memcpy(receipt.path,p->files.paths[0],n+1);receipt.file=p->files.generated[0];receipt.owner=getpid();receipt.valid=1;
  if(!wr_iot_restart_profile_receipt_current(&receipt))goto done;
  s->profile=receipt;
 }
 if(!wr_iot_restart_profile_receipt_current(&s->profile))goto done;
 if(!s->wan.owner&&!wr_iot_wan_followup_capture(&s->wan,1))goto done;
 ok=s->wan.owner==getpid()&&s->wan.radio_on==1&&!s->wan.attempted&&!s->wan.returned&&
  s->wan.plan>=WR_WAN_NONE&&s->wan.plan<=WR_WAN_RECONNECT&&
  wr_iot_rc_restart_wan_current(1,s->wan.plan)&&cold_disabled_release_bound(s)&&
  wr_iot_restart_profile_receipt_current(&s->profile);
 done:s->busy=0;return ok;
}
int wr_iot_cold_disabled_release_begin(struct wr_iot_cold_disabled_release *s,
 struct wr_iot_cold_disabled *disabled)
{
 struct wr_iot_cold_owner *p;
 if(!s||!disabled||s->owner||s->busy||s->disabled||s->parent||s->profile.valid||s->wan.owner||
    !wr_iot_cold_disabled_current(disabled))return 0;
 p=disabled->parent;s->owner=getpid();s->disabled=disabled;s->parent=p;s->identity=p->main.identity;
 memcpy(s->id,disabled->idle.id,sizeof(s->id));s->created=disabled->idle.created;
 s->policy.owner=getpid();s->policy.guest=p->guest.desired;s->policy.isolate=p->guest.isolate;
 s->policy.services=p->services.policy;s->policy.multicast=p->multicast.policy;
 (void)wr_iot_cold_disabled_release_current(s);return 1;
}
