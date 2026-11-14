#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "rebind-owner.h"
#include "rc-shutdown-admission.h"
int wr_iot_rebind_owner_begin(struct wr_iot_rebind_owner *s,
 const struct wr_iot_control_request *request,const struct wr_iot_physical_stop_request *physical,
 int router,int radio,int mode)
{
 int admitted;
 if(!s||s->owner||s->busy||s->phase!=WR_REBIND_OWNER_IDLE||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 s->busy=1;
 admitted=wr_iot_rebind_runner_begin(&s->start,request,physical,router,radio,mode);
 if(s->start.owner){
  s->owner=getpid();s->phase=s->start.phase==WR_IOT_RUN_REJECTED?
   WR_REBIND_OWNER_REJECTED:WR_REBIND_OWNER_START;
 }
 s->busy=0;return admitted;
}
enum wr_iot_result_state wr_iot_rebind_owner_execute(struct wr_iot_rebind_owner *s,
 const struct wr_iot_control_request *request)
{
 enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
 if(!s||!request||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active)return result;
 if(s->phase==WR_REBIND_OWNER_START||s->phase==WR_REBIND_OWNER_STOP)return result;
 if(!request->created||!memchr(request->id,0,sizeof(request->id))||
    !wr_iot_control_id(request->id))return WR_IOT_RESULT_REJECTED;
 if(s->phase!=WR_REBIND_OWNER_ACTIVE||request->request.enabled!=0)
  return WR_IOT_RESULT_REJECTED;
 s->busy=1;
 if(wr_iot_rebind_active_stop_begin(&s->stop,&s->start,request))s->phase=WR_REBIND_OWNER_STOP;
 else result=WR_IOT_RESULT_REJECTED;
 s->busy=0;return result;
}
enum wr_iot_result_state wr_iot_rebind_owner_continue(struct wr_iot_rebind_owner *s,
 const char *id,unsigned long long created)
{
 enum wr_iot_result_state result=WR_IOT_RESULT_RECOVERY;
 if(!s||!id||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active||
    !created||!wr_iot_control_id(id))return result;
 s->busy=1;
 if(s->phase==WR_REBIND_OWNER_START){
  result=wr_iot_rebind_runner_continue(&s->start,id,created);
  if(result==WR_IOT_RESULT_APPLIED)s->phase=WR_REBIND_OWNER_ACTIVE;
  else if(result==WR_IOT_RESULT_REJECTED)s->phase=WR_REBIND_OWNER_REJECTED;
 }else if(s->phase==WR_REBIND_OWNER_STOP){
  result=wr_iot_rebind_active_stop_continue(&s->stop,id,created);
  if(result==WR_IOT_RESULT_APPLIED)s->phase=WR_REBIND_OWNER_OFF;
 }else if(s->phase==WR_REBIND_OWNER_ACTIVE||s->phase==WR_REBIND_OWNER_REJECTED){
  if(!strcmp(id,s->start.input.id)&&created==s->start.input.created)
   result=s->phase==WR_REBIND_OWNER_ACTIVE?WR_IOT_RESULT_APPLIED:WR_IOT_RESULT_REJECTED;
 }else if(s->phase==WR_REBIND_OWNER_OFF&&
          !strcmp(id,s->stop.id)&&created==s->stop.created)result=WR_IOT_RESULT_APPLIED;
 s->busy=0;return result;
}
int wr_iot_rebind_owner_observed(const struct wr_iot_rebind_owner *s,
 const struct wr_iot_control_result *result)
{
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->phase==WR_REBIND_OWNER_ACTIVE)return wr_iot_rebind_active_observed(&s->start,result);
 if(s->phase==WR_REBIND_OWNER_OFF)return wr_iot_rebind_off_observed(&s->start,&s->stop,result);
 return 0;
}
int wr_iot_rebind_owner_closed(const struct wr_iot_rebind_owner *s,
 const struct wr_iot_control_result *result,struct wr_iot_driver_closed_result *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_REBIND_OWNER_OFF)return 0;
 return wr_iot_rebind_off_closed(&s->start,&s->stop,result,out);
}
