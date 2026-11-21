#include <string.h>
#include <unistd.h>
#include "activation-owner.h"
#include "reopen-admission.h"
#include "service-guard.h"
#include "bridge.h"
#include "dns-activation.h"
#include <net/if.h>
#include "rc-shutdown-admission.h"
static enum wr_iot_result_state owner_start_result(struct wr_iot_activation_owner *s,
 enum wr_iot_result_state result)
{
 if(result==WR_IOT_RESULT_APPLIED)s->phase=WR_IOT_OWNER_ACTIVE;
 else if(result==WR_IOT_RESULT_REJECTED)s->phase=WR_IOT_OWNER_REJECTED;
 return result;
}
/* Only completed, unowned contexts may be copied for a failed admission.
 * The new runner itself always starts in its stable final address. */
static enum wr_iot_result_state owner_reopen(struct wr_iot_activation_owner *s,
 const struct wr_iot_control_request *r,int router,int radio,int mode)
{
 struct wr_iot_reopen_witness witness={0};
 struct wr_iot_start_runner stopped;
 struct wr_iot_active_stop stop;
 enum wr_iot_activation_owner_phase phase=s->phase;
 enum wr_iot_result_state result=WR_IOT_RESULT_REJECTED;
 int guard;
 if(r->request.enabled!=1||wr_iot_rc_shutdown.pending||
    !strcmp(r->id,s->start.input.id)||!strcmp(r->id,s->stop.id)||
    r->created<s->start.input.created||r->created<s->stop.created)return result;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return WR_IOT_RESULT_RECOVERY;
 s->busy=1;
 if(phase==WR_IOT_OWNER_OFF){
  if(!wr_iot_reopen_witness_take(&witness,&s->start,&s->stop))goto done;
 }else{
  /* A rejected pre-OPEN attempt retains the previous CLOSED witness.
   * An attempted OPEN requires a new CLOSE witness; never use initial idle. */
  if(s->start.prior_closed.submitted){
   if(!wr_iot_reopen_recovered_witness_take(&witness,&s->start))goto done;
  }else{
  if(s->start.phase!=WR_IOT_RUN_REJECTED||
     s->start.admission.snapshot.active||s->start.admission.snapshot.token||
     !s->start.prior_closed.valid||s->start.prior_closed.submitted||
     !wr_iot_request_disabled_current()||if_nametoindex("br-iot")||
     !wr_iot_bss_is_down()||wr_iot_dns_activation_recovery_state()!=0||
     !wr_iot_reopen_witness_current(&s->start.prior_closed))goto done;
  witness=s->start.prior_closed;
  }
 }
 stopped=s->start;stop=s->stop;
 memset(&s->start,0,sizeof(s->start));memset(&s->stop,0,sizeof(s->stop));
 if(wr_iot_start_runner_begin_reopen(&s->start,r,router,radio,mode,&witness)){
  s->phase=WR_IOT_OWNER_START;result=WR_IOT_RESULT_RECOVERY;
 }else if(s->start.owner){
  s->phase=WR_IOT_OWNER_START;result=WR_IOT_RESULT_RECOVERY;
  if(s->start.phase==WR_IOT_RUN_REJECTED)
   result=owner_start_result(s,WR_IOT_RESULT_REJECTED);
 }else{
  s->start=stopped;s->stop=stop;
  if(s->stop.active)s->stop.active=&s->start;
  s->phase=phase;
 }
 done:s->busy=0;wr_iot_service_guard_leave(guard);return result;
}
enum wr_iot_result_state wr_iot_activation_owner_execute(struct wr_iot_activation_owner *s,
 const struct wr_iot_control_request *request,int router,int radio,int mode)
{
 enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
 if(!s||!request||s->busy||(s->owner&&s->owner!=getpid())||
    !wr_iot_rc_shutdown.active)return WR_IOT_RESULT_RECOVERY;
 if(s->phase==WR_IOT_OWNER_START||s->phase==WR_IOT_OWNER_STOP)
  return WR_IOT_RESULT_RECOVERY;
 if(!request->created||!memchr(request->id,0,sizeof(request->id))||
    !wr_iot_control_id(request->id))return WR_IOT_RESULT_REJECTED;
 if(s->phase==WR_IOT_OWNER_INITIAL_OFF&&!strcmp(request->id,s->initial_off.id))return WR_IOT_RESULT_REJECTED;
 if((s->phase==WR_IOT_OWNER_IDLE||s->phase==WR_IOT_OWNER_INITIAL_OFF)&&request->request.enabled==0){
  struct wr_iot_initial_off initial={0};
  s->busy=1;
  if(wr_iot_initial_off_begin(&initial,request)){
   s->initial_off=initial;s->owner=getpid();s->phase=WR_IOT_OWNER_INITIAL_OFF;
   result=WR_IOT_RESULT_APPLIED;
  }else result=WR_IOT_RESULT_REJECTED;
  s->busy=0;return result;
 }
 if(s->phase==WR_IOT_OWNER_ACTIVE){
  s->busy=1;
  if(wr_iot_active_stop_begin(&s->stop,&s->start,request))s->phase=WR_IOT_OWNER_STOP;
  else result=WR_IOT_RESULT_REJECTED;
  s->busy=0;return result;
 }
 if(s->phase==WR_IOT_OWNER_OFF||
    (s->phase==WR_IOT_OWNER_REJECTED&&s->start.prior_closed.valid))
  return owner_reopen(s,request,router,radio,mode);
 if(s->phase!=WR_IOT_OWNER_IDLE&&s->phase!=WR_IOT_OWNER_REJECTED&&s->phase!=WR_IOT_OWNER_INITIAL_OFF)
  return WR_IOT_RESULT_REJECTED;
 if(request->request.enabled!=1)return WR_IOT_RESULT_REJECTED;
 if(s->phase==WR_IOT_OWNER_REJECTED){
  if(s->start.phase!=WR_IOT_RUN_REJECTED||s->start.admission.snapshot.active||
     s->start.admission.snapshot.token)return WR_IOT_RESULT_RECOVERY;
  /* No owned startup resources remain after proved rollback. A different
   * envelope may start anew; never replay the previous transaction identity. */
  if(!strcmp(request->id,s->start.input.id))return WR_IOT_RESULT_REJECTED;
  memset(&s->start,0,sizeof(s->start));
 }
 s->owner=getpid();s->busy=1;
 if(wr_iot_start_runner_begin(&s->start,request,router,radio,mode))s->phase=WR_IOT_OWNER_START;
 else if(s->start.owner){
  s->phase=WR_IOT_OWNER_START;
  if(s->start.phase==WR_IOT_RUN_REJECTED)
   result=owner_start_result(s,WR_IOT_RESULT_REJECTED);
 }else {s->phase=WR_IOT_OWNER_IDLE;result=WR_IOT_RESULT_REJECTED;}
 s->busy=0;return result;
}
enum wr_iot_result_state wr_iot_activation_owner_continue(struct wr_iot_activation_owner *s,
 const char *id,unsigned long long created)
{
 enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
 if(!s||!id||!created||s->owner!=getpid()||s->busy||
    !wr_iot_rc_shutdown.active)return result;
 s->busy=1;
 switch(s->phase){
 case WR_IOT_OWNER_START:
  result=owner_start_result(s,wr_iot_start_runner_continue(&s->start,id,created));break;
 case WR_IOT_OWNER_STOP:
  result=wr_iot_active_stop_continue(&s->stop,id,created);
  if(result==WR_IOT_RESULT_APPLIED)s->phase=WR_IOT_OWNER_OFF;
  break;
 case WR_IOT_OWNER_INITIAL_OFF:
  if(wr_iot_control_id(id)&&!strcmp(id,s->initial_off.id)&&created==s->initial_off.created)
   result=WR_IOT_RESULT_APPLIED;
  break;
 case WR_IOT_OWNER_ACTIVE:
 case WR_IOT_OWNER_REJECTED:
  if(wr_iot_control_id(id)&&!strcmp(id,s->start.input.id)&&created==s->start.input.created)
   result=s->phase==WR_IOT_OWNER_ACTIVE?WR_IOT_RESULT_APPLIED:WR_IOT_RESULT_REJECTED;
  break;
 case WR_IOT_OWNER_OFF:
  if(wr_iot_control_id(id)&&!strcmp(id,s->stop.id)&&created==s->stop.created)
   result=WR_IOT_RESULT_APPLIED;
  break;
 default:break;
 }
 s->busy=0;return result;
}
