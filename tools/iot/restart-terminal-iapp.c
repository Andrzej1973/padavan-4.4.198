#define _GNU_SOURCE
#include <unistd.h>
#include <signal.h>
#include "restart-terminal-iapp.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
int wr_iot_terminal_iapp_begin(struct wr_iot_terminal_iapp*s,struct wr_iot_iapp_child*child)
{
 if(!s||!child||s->owner||s->busy||child->owner||child->attempted||
    !wr_iot_iapp_child_closed(child)||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 if(!wr_iot_radio_stop_fence_begin(&s->fence))return 0;
 s->owner=getpid();s->child=child;
 s->guard=wr_iot_service_guard_enter(1);
 /* Even guard refusal owns a fence; step must balance it before retry/reuse. */
 return 1;
}
static void terminal_cleanup(void*data)
{
 struct wr_iot_terminal_iapp*s=data;
 if(s->guard==1)wr_iot_service_guard_leave(1);
 s->guard=0;s->child=NULL;s->busy=0;
}
int wr_iot_terminal_iapp_step(struct wr_iot_terminal_iapp*s)
{
 sigset_t queued;int result;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->result&&!s->child)return s->result;
 if(!s->child||!wr_iot_rc_shutdown.active)return 0;
 s->busy=1;
 if(!sigpending(&queued)){
  if(sigismember(&queued,SIGTERM)==1)(void)wr_iot_rc_shutdown_note(SIGTERM);
#ifdef SIGQUIT
  else if(sigismember(&queued,SIGQUIT)==1)(void)wr_iot_rc_shutdown_note(SIGQUIT);
#endif
 }
 if(s->guard!=1||(!s->attempted&&wr_iot_rc_shutdown.pending))result=-1;
 else{
  if(!s->attempted){
   s->attempted=1;(void)wr_iot_iapp_child_begin(s->child);
   s->busy=0;return 0;
  }
  if(!wr_iot_iapp_child_closed(s->child))(void)wr_iot_iapp_child_step(s->child);
  if(!wr_iot_iapp_child_closed(s->child)){s->busy=0;return 0;}
  result=s->child->result==1?1:-1;
 }
 s->result=result;
 if(!wr_iot_radio_stop_fence_end_cleanup(&s->fence,terminal_cleanup,s)){
  s->busy=0;return 0;
 }
 return result;
}
