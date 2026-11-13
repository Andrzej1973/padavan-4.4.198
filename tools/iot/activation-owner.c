#include <string.h>
#include <unistd.h>
#include "activation-owner.h"
#include "rc-shutdown-admission.h"
static enum wr_iot_result_state owner_start_result(struct wr_iot_activation_owner *s,
 enum wr_iot_result_state result)
{
 if(result==WR_IOT_RESULT_APPLIED)s->phase=WR_IOT_OWNER_ACTIVE;
 else if(result==WR_IOT_RESULT_REJECTED)s->phase=WR_IOT_OWNER_REJECTED;
 return result;
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
 if(s->phase==WR_IOT_OWNER_ACTIVE){
  s->busy=1;
  if(wr_iot_active_stop_begin(&s->stop,&s->start,request))s->phase=WR_IOT_OWNER_STOP;
  else result=WR_IOT_RESULT_REJECTED;
  s->busy=0;return result;
 }
 if(s->phase!=WR_IOT_OWNER_IDLE&&s->phase!=WR_IOT_OWNER_REJECTED)
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
