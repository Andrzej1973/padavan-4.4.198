#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-root.h"
#include "cold-on-root-recovery.h"
#include "cold-on-root-signal.h"
#include "rc-shutdown-admission.h"
int wr_iot_cold_root_begin(struct wr_iot_cold_root *s,
 const struct wr_iot_control_request *input,int reload)
{
 if(!s||!input||s->owner||s->busy||s->phase!=WR_COLD_ROOT_IDLE||
    s->parent.owner||s->handoff.owner||s->release.owner||s->released.release||
    s->terminal.owner||s->disabled.owner||s->disabled_release.owner||
    s->disabled_released.release||s->disabled_terminal.owner||s->stop.owner||
    s->stop.busy||s->stop.parent||s->stop.handoff||s->stop.off.owner||
    s->stop.off_attempted||s->stop.phase!=WR_COLD_STOP_IDLE)return 0;
 s->busy=1;
 if(!wr_iot_cold_owner_begin(&s->parent,input,reload)){s->busy=0;return 0;}
 s->owner=getpid();s->enabled=input->request.enabled;
 s->phase=s->parent.phase==WR_COLD_OWNER_RETAINED?WR_COLD_ROOT_RETAINED:WR_COLD_ROOT_PREPARE;
 s->busy=0;return 1;
}
int wr_iot_cold_root_step(struct wr_iot_cold_root *s)
{
 int result=0,ready,signal_result;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 signal_result=wr_iot_cold_root_signal_step(s);
 if(signal_result<=0)return signal_result;
 if(s->phase==WR_COLD_ROOT_RETAINED&&!s->parent.generation.main_may_have_started)
  return wr_iot_cold_root_preup_recover(s)?-1:0;
 s->busy=1;
 switch(s->phase){
 case WR_COLD_ROOT_PREPARE:
  if(wr_iot_cold_owner_step(&s->parent))s->phase=WR_COLD_ROOT_HANDOFF;
  else if(s->parent.phase==WR_COLD_OWNER_RETAINED||s->parent.phase==WR_COLD_OWNER_RESTORED)
   s->phase=WR_COLD_ROOT_RETAINED;
  break;
 case WR_COLD_ROOT_HANDOFF:
  if(s->enabled){
   if(wr_iot_cold_handoff_begin(&s->handoff,&s->parent))
    s->phase=s->handoff.backend_claimed?WR_COLD_ROOT_WAIT:WR_COLD_ROOT_RETAINED;
  }else{
   /* begin may claim an OFF observer and then fail a fresh proof. Retain
    * that same observer; never call begin again once it owns state. */
   ready=s->disabled.owner?wr_iot_cold_disabled_current(&s->disabled):
    wr_iot_cold_disabled_begin(&s->disabled,&s->parent);
   if(ready)s->phase=WR_COLD_ROOT_CAPTURE;
  }
  break;
 case WR_COLD_ROOT_WAIT:
  if(wr_iot_cold_handoff_step(&s->handoff))s->phase=WR_COLD_ROOT_CAPTURE;
  break;
 case WR_COLD_ROOT_CAPTURE:
  if(s->enabled){
   ready=s->release.owner?wr_iot_cold_release_current(&s->release):
    wr_iot_cold_release_begin(&s->release,&s->handoff);
  }else{
   ready=s->disabled_release.owner?wr_iot_cold_disabled_release_current(&s->disabled_release):
    wr_iot_cold_disabled_release_begin(&s->disabled_release,&s->disabled);
  }
  /* The release wrapper independently repeats complete capture/current
   * proof, even when begin reports ownership rather than readiness. */
  if(ready)s->phase=WR_COLD_ROOT_RELEASE;
  break;
 case WR_COLD_ROOT_RELEASE:
  ready=s->enabled?wr_iot_rc_cold_parent_release(&s->released,&s->release):
   wr_iot_rc_cold_disabled_parent_release(&s->disabled_released,&s->disabled_release);
  if(ready)s->phase=WR_COLD_ROOT_TERMINAL_BEGIN;
  break;
 case WR_COLD_ROOT_TERMINAL_BEGIN:
  ready=s->enabled?wr_iot_rc_cold_terminal_begin(&s->terminal,&s->released):
   wr_iot_rc_cold_disabled_terminal_begin(&s->disabled_terminal,&s->disabled_released);
  if(ready)s->phase=WR_COLD_ROOT_TERMINAL;
  break;
 case WR_COLD_ROOT_TERMINAL:
 case WR_COLD_ROOT_DONE:
  ready=s->enabled?wr_iot_rc_cold_terminal_step(&s->terminal):
   wr_iot_rc_cold_disabled_terminal_step(&s->disabled_terminal);
  if(ready){s->phase=WR_COLD_ROOT_DONE;result=1;}
  break;
 default:break;
 }
 s->busy=0;return result;
}
int wr_iot_cold_root_retire(struct wr_iot_cold_root *s)
{
 volatile unsigned char *bytes;size_t n;int ready;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_COLD_ROOT_DONE)return 0;
 s->busy=1;
 ready=s->enabled?wr_iot_rc_cold_terminal_retire(&s->terminal):
  wr_iot_rc_cold_disabled_terminal_retire(&s->disabled_terminal);
 if(!ready){s->busy=0;return 0;}
 bytes=(volatile unsigned char *)s;n=sizeof(*s);while(n--)*bytes++=0;
 return 1;
}
