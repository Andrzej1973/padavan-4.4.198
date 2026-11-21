#define _GNU_SOURCE
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "cold-on-root-signal.h"
#include "cold-on-root-recovery.h"
#include "precreated-entropy.h"
#include "rc-shutdown-admission.h"
static void cold_signal_wipe(void *p,size_t n)
{volatile unsigned char *b=p;while(n--)*b++=0;}
int wr_iot_cold_root_signal_step(struct wr_iot_cold_root *s)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request off={0};unsigned char entropy[32]={0};
 struct timespec now;sigset_t queued;unsigned i,nonzero=0;int result=0,final;
 const char *original_id;unsigned long long created;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(wr_iot_rc_shutdown.active){
  if(sigpending(&queued))return 0;
  if(sigismember(&queued,SIGTERM)==1)(void)wr_iot_rc_shutdown_note(SIGTERM);
#ifdef SIGQUIT
  else if(sigismember(&queued,SIGQUIT)==1)(void)wr_iot_rc_shutdown_note(SIGQUIT);
#endif
 }
 /* A signal after parent release has a route slot, not active pending.
  * Never start a new IAPP transaction that this slot deliberately excludes.
  * The private handoff owns all validation and retains on any uncertainty. */
 if(!wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.normal_route_requested&&
    s->enabled==1&&(s->phase==WR_COLD_ROOT_TERMINAL_BEGIN||
     (s->phase==WR_COLD_ROOT_TERMINAL&&!s->terminal.terminal.attempted)))
  return wr_iot_rc_cold_root_routed_handoff(s)?-1:0;
 if(!wr_iot_rc_shutdown.pending)return 1;
 if(!wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    ))return 0;
 final=s->phase==WR_COLD_ROOT_TERMINAL;
 if(final){
  if(!s->enabled||s->final_off_attempted||!s->terminal.terminal.shutdown_held||
     !wr_iot_iapp_child_closed(&s->terminal.child))
   return wr_iot_rc_cold_root_final_shutdown(s,NULL)?-1:0;
  if(s->enabled!=1||!s->released.released||s->released.busy||
     s->released.release!=&s->release||s->release.owner!=getpid()||s->release.busy||
     s->release.parent||s->release.handoff||!s->release.created||
     !memchr(s->release.id,0,sizeof(s->release.id))||!wr_iot_control_id(s->release.id)||
     !wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
  original_id=s->release.id;created=s->release.created;
 }else{
 if(!s->parent.generation.main_may_have_started)
  return wr_iot_cold_root_preup_recover(s)?-1:0;
 if(!s->handoff.owner||!s->handoff.backend_claimed||s->stop.owner)
  return wr_iot_cold_root_shutdown(s,NULL)?-1:0;
 if(!s->enabled||s->parent.owner!=getpid()||s->parent.busy||
    s->handoff.owner!=getpid()||s->handoff.busy||s->handoff.parent!=&s->parent||
    !s->handoff.attempted||!s->handoff.backend_claimed||!s->handoff.created||
    !memchr(s->handoff.id,0,sizeof(s->handoff.id))||!wr_iot_control_id(s->handoff.id)||
    !wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned)return 0;
 original_id=s->handoff.id;created=s->handoff.created;
 }
 /* No blocking entropy wait, predictable fallback or timestamp substitution.
  * Failure retains the same parent; no OFF/backend command was submitted. */
 if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    (unsigned long long)now.tv_sec<created||
    wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy))goto done;
 for(i=0;i<16;i++){
  nonzero|=entropy[i];off.id[2*i]=hex[entropy[i]>>4];off.id[2*i+1]=hex[entropy[i]&15];
 }
 if(!nonzero||!strcmp(off.id,original_id))goto done;
 off.created=(unsigned long long)now.tv_sec;
 if(final?wr_iot_rc_cold_root_final_shutdown(s,&off):wr_iot_cold_root_shutdown(s,&off))result=-1;
 done:cold_signal_wipe(entropy,sizeof(entropy));cold_signal_wipe(&off,sizeof(off));return result;
}
