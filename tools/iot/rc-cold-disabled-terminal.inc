/* Uncomposed private RC completion owner. Include after cold followup observer.
 * IAPP gate must be the paired source policy, never a request-controlled bit. */
#include "restart-terminal-iapp.h"
#include "restart-iapp-policy.h"
#include "cold-on-disabled-release.h"
#include "rc-cold-disabled-completion.h"
static int wr_iot_cold_disabled_terminal_begin(struct wr_iot_cold_disabled_terminal *s,
 struct wr_iot_cold_disabled_parent_release *released)
{
 if(!s||!released||s->owner||s->busy||s->phase!=WR_COLD_DISABLED_TERM_IDLE||s->parent_release||
    s->terminal.owner||s->child.owner||!released->released||released->busy||!released->release||
    !wr_iot_cold_disabled_followup_current(released->release))return 0;
 s->owner=getpid();s->parent_release=released;s->phase=WR_COLD_DISABLED_TERM_WAN;return 1;
}
static int wr_iot_cold_disabled_terminal_step(struct wr_iot_cold_disabled_terminal *s)
{
 struct wr_iot_cold_disabled_release *r;int terminal,result=0;
 if(!s||s->owner!=getpid()||s->busy||!s->parent_release||!s->parent_release->released||
    s->parent_release->busy||!s->parent_release->release)return 0;
 r=s->parent_release->release;s->busy=1;
 /* Drain the one owned child even while its own fence has active admission.
  * Never hide an unknown pipe result by initializing a replacement child. */
 if(s->phase==WR_COLD_DISABLED_TERM_IAPP){
  terminal=wr_iot_terminal_iapp_step(&s->terminal);
  if(terminal<0)s->phase=WR_COLD_DISABLED_TERM_RETAINED;
  else if(terminal==1&&wr_iot_iapp_child_closed(&s->child)&&s->child.result==1&&
          !s->terminal.child&&!s->terminal.guard&&!s->terminal.fence.owner&&
          !s->terminal.fence.level&&wr_iot_cold_disabled_followup_current(r)){
   s->phase=WR_COLD_DISABLED_TERM_DONE;result=1;
  }
  goto done;
 }
 if(!wr_iot_cold_disabled_followup_current(r))goto done;
 if(s->phase==WR_COLD_DISABLED_TERM_DONE){result=1;goto done;}
 if(s->phase==WR_COLD_DISABLED_TERM_WAN){
  if(!wr_iot_cold_disabled_followup_wan(r))goto done;
  if(!s->led_attempted){s->led_attempted=1;s->led_returned=wr_iot_rc_restart_led_on()==1;}
  if(!s->led_returned){s->phase=WR_COLD_DISABLED_TERM_RETAINED;goto done;}
  s->phase=WR_COLD_DISABLED_TERM_IAPP_PENDING;goto done;
 }
#if WR_IOT_IAPP_POLICY_PREPARED
 if(s->phase==WR_COLD_DISABLED_TERM_IAPP_PENDING&&s->led_returned&&!s->terminal.owner&&
    wr_iot_terminal_iapp_begin(&s->terminal,&s->child)){
  s->terminal.defer_pending_shutdown=1;s->phase=WR_COLD_DISABLED_TERM_IAPP;
 }
#endif
 done:s->busy=0;return result;
}
/* No live child/fence/guard remains. Preserve the inert INITIAL_OFF backend;
 * discard only completed nonsecret followup state and its process exclusion. */
static int wr_iot_cold_disabled_terminal_retire(struct wr_iot_cold_disabled_terminal *s)
{
 struct wr_iot_cold_disabled_parent_release *parent_release;struct wr_iot_cold_disabled_release *r;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_COLD_DISABLED_TERM_DONE||!s->parent_release||
    !s->led_attempted||!s->led_returned||!wr_iot_iapp_child_closed(&s->child)||s->child.result!=1||
    s->terminal.busy||s->terminal.child||s->terminal.guard||s->terminal.fence.owner||s->terminal.fence.level||
    s->terminal.result!=1)return 0;
 parent_release=s->parent_release;r=parent_release->release;
 if(!parent_release->released||parent_release->busy||!r||
    !r->wan.attempted||!r->wan.returned||!wr_iot_cold_disabled_followup_current(r))return 0;
 wr_iot_cold_disabled_wipe(r,sizeof(*r));
 wr_iot_cold_disabled_wipe(parent_release,sizeof(*parent_release));
 wr_iot_cold_disabled_wipe(s,sizeof(*s));
 wr_iot_rc_shutdown.radio_on_owned=0;return 1;
}
