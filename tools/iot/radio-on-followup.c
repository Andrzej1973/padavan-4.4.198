#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "radio-on-followup.h"
#include "control-record.h"
#include "rc-backend.h"
#include "restart-iapp-policy.h"
#include "rc-shutdown-admission.h"
static int on_followup_network(struct wr_iot_on_restore *s)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_result r={0};unsigned i;
 if(!s->handoff_created||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_off_owned)return 0;
 for(i=0;i<16;i++){r.id[2*i]=hex[s->open_id[i]>>4];r.id[2*i+1]=hex[s->open_id[i]&15];}
 r.created=s->handoff_created;r.state=WR_IOT_RESULT_APPLIED;
 return wr_iot_rc_backend_observed(&r);
}
int wr_iot_on_followup_step(struct wr_iot_on_restore *s)
{
 int result=0,terminal;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->phase==WR_ON_RESTORE_DONE)return on_followup_network(s);
 s->busy=1;
 /* Drain existing child even while its terminal fence/admission is active. */
 if(s->phase==WR_ON_RESTORE_IAPP){
  terminal=wr_iot_terminal_iapp_step(&s->terminal);
  if(terminal<0)s->phase=WR_ON_RESTORE_RETAINED;
  else if(terminal==1&&wr_iot_iapp_child_closed(&s->child)&&s->child.result==1&&
          !s->terminal.child&&!s->terminal.guard&&!s->terminal.fence.owner&&
          !s->terminal.fence.level&&on_followup_network(s)){
   s->phase=WR_ON_RESTORE_DONE;result=1;
  }
  goto done;
 }
 if(wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned)goto done;
 if(s->phase==WR_ON_RESTORE_RELEASED){
  if(s->generation.admission||s->generation.phase!=WR_ON_GEN_COMMITTED||
     s->wan.owner!=getpid()||s->wan.radio_on!=1||s->wan.attempted||s->wan.returned)goto done;
  s->phase=WR_ON_RESTORE_WAN;goto done;
 }
 if(s->phase==WR_ON_RESTORE_WAN){
  if(!wr_iot_wan_followup_step(&s->wan)||!on_followup_network(s))goto done;
  if(!s->led_attempted){s->led_attempted=1;s->led_returned=wr_iot_rc_restart_led_on()==1;}
  if(!s->led_returned){s->phase=WR_ON_RESTORE_RETAINED;goto done;}
  s->phase=WR_ON_RESTORE_IAPP_PENDING;goto done;
 }
#if WR_IOT_IAPP_POLICY_PREPARED
 if(s->phase==WR_ON_RESTORE_IAPP_PENDING&&s->led_returned&&on_followup_network(s)&&
    !s->terminal.owner&&wr_iot_terminal_iapp_begin(&s->terminal,&s->child))s->phase=WR_ON_RESTORE_IAPP;
#endif
 done:s->busy=0;return result;
}
