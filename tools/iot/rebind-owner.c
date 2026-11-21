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
int wr_iot_rebind_owner_restart(struct wr_iot_rebind_owner *s,
 const struct wr_iot_control_request *request,const struct wr_iot_physical_stop_request *physical,
 int router,int radio,int mode)
{
 struct wr_iot_rebind_owner previous;int admitted;
 if(!s||!request||!physical||s->owner!=getpid()||s->busy||s->phase!=WR_REBIND_OWNER_OFF||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    physical->action!=WR_STOP_RELEASE||!wr_iot_physical_stop_request_valid(physical)||
    request->request.enabled!=1||!request->created||
    !memchr(request->id,0,sizeof(request->id))||!wr_iot_control_id(request->id)||
    !strcmp(request->id,s->start.input.id)||!strcmp(request->id,s->stop.id)||
    request->created<s->start.input.created||request->created<s->stop.created||
    s->start.owner!=getpid()||s->start.busy||s->start.phase!=WR_IOT_RUN_STOPPED||
    s->start.start.admission.snapshot.active||s->start.start.admission.snapshot.token||
    s->stop.owner!=getpid()||s->stop.busy||!s->stop.complete||s->stop.active!=&s->start||
    s->stop.stop.phase!=WR_IOT_STOP_COMPLETE||s->stop.stop.guard||
    s->stop.stop.close.phase!=WR_IOT_CLOSE_OWNER_RELEASED||
    s->stop.stop.disable.services.settings.active||s->stop.stop.disable.services.settings.token||
    s->stop.stop.disable.radio.active||s->stop.stop.disable.radio.files.count||
    s->start.stop.owner||s->start.stop.guard||s->start.close.owner||s->start.rollback.owner||
    physical->epoch!=s->start.open.attempt.identity.adapter_epoch||
    physical->generation!=s->start.open.attempt.identity.device_generation||
    physical->open_token!=s->stop.stop.close.request.open_token||
    physical->closed_serial!=s->stop.stop.close_serial)return 0;
 /* Old OFF is completed provenance only after physical restart. A fresh old
  * epoch read would be invalid. The new runner verifies RELEASE/new Main.
  * All snapshots/guards above are released: this backup is inactive metadata,
  * matching the existing ordinary-reopen rollback discipline, never live IO. */
 previous=*s;memset(s,0,sizeof(*s));
 admitted=wr_iot_rebind_owner_begin(s,request,physical,router,radio,mode);
 if(!s->owner||(s->phase==WR_REBIND_OWNER_REJECTED&&
    !s->start.start.admission.snapshot.active&&!s->start.start.admission.snapshot.token&&
    !s->start.start.admission.admitted&&!s->start.start.admission.mutation_started&&
    !s->start.open.owner&&s->start.open.phase==WR_REBIND_OPEN_IDLE)){
  /* A read-only refusal owns no new host resources. Restore exact completion
   * and repair its sole internal pointer; do not synthesize a new receipt. */
  *s=previous;s->stop.active=&s->start;return 0;
 }
 return admitted;
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
