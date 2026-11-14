#include <time.h>
#include <string.h>
#include "control-channel.h"
#include "rc-backend.h"
#include "rc-quiesce.h"
#include "activation-observe.h"
#include "service-guard.h"
#include "rc-shutdown-admission.h"
#include "radio-stop-contract.h"
#include "precreated-entropy.h"
static struct wr_iot_activation_owner backend;
enum wr_iot_result_state wr_iot_activation_execute(const struct wr_iot_control_request *request)
{
 struct wr_iot_rc_mode mode={0};enum wr_iot_result_state result;
 int guard;
 if(!request)return WR_IOT_RESULT_REJECTED;
 if(!wr_iot_rc_shutdown.active)return WR_IOT_RESULT_RECOVERY;
 /* Never let a failed new mode observation turn an already retained recovery
  * into a terminal rejection. Only continuation can advance that owner. */
 if(backend.phase==WR_IOT_OWNER_START||backend.phase==WR_IOT_OWNER_STOP)
  return WR_IOT_RESULT_RECOVERY;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return WR_IOT_RESULT_REJECTED;
 if(request->request.enabled==1&&wr_iot_rc_mode_read(&mode)!=1){
  wr_iot_service_guard_leave(guard);return WR_IOT_RESULT_REJECTED;
 }
 result=wr_iot_activation_owner_execute(&backend,request,mode.router,mode.radio,mode.mode);
 wr_iot_service_guard_leave(guard);return result;
}
enum wr_iot_result_state wr_iot_activation_continue(const char *id,unsigned long long created)
{
 return wr_iot_activation_owner_continue(&backend,id,created);
}
int wr_iot_rc_backend_observed(const struct wr_iot_control_result *result)
{
 return wr_iot_activation_owner_observed(&backend,result);
}

int wr_iot_activation_prepare_radio_stop(void)
{
 struct wr_iot_initial_off initial={0};
 struct wr_iot_control_request request={0};
 struct timespec now;unsigned char random[32];int guard,ok=0;
 static const char hex[]="0123456789abcdef";
 if(!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||backend.busy)return 0;
 /* A completed software CLOSE is not a physical-radio drain certificate.
  * Only the never-opened case is currently admitted; retain every other
  * owner's context and isolation without replaying or synthesizing OFF. */
 if(backend.phase!=WR_IOT_OWNER_IDLE&&backend.phase!=WR_IOT_OWNER_INITIAL_OFF)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 /* A physical restart may replace the adapter after a previous INITIAL_OFF.
  * Capture a new never-opened proof each time. The old public OFF result keeps
  * its own identity and must not become a lease for the replacement adapter. */
 if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    wr_iot_precreated_entropy(NULL,random,sizeof(random))!=(int)sizeof(random))goto done;
 for(unsigned i=0;i<16;i++){
  request.id[2*i]=hex[random[i]>>4];request.id[2*i+1]=hex[random[i]&15];
 }
 request.created=(unsigned long long)now.tv_sec;
 ok=wr_iot_initial_off_begin(&initial,&request);
 done:wr_iot_service_guard_leave(guard);return ok==1;
}

int wr_iot_rc_backend_closed(struct wr_iot_driver_closed_result *out)
{
 struct wr_iot_control_result result={0};
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(backend.phase!=WR_IOT_OWNER_OFF||backend.busy)return 0;
 memcpy(result.id,backend.stop.id,sizeof(result.id));
 result.created=backend.stop.created;result.state=WR_IOT_RESULT_APPLIED;
 return wr_iot_activation_owner_closed(&backend,&result,out);
}

int wr_iot_rc_quiesce_begin(struct wr_iot_rc_quiesce *s,
 const struct wr_iot_control_request *off)
{
 struct wr_iot_control_result observed={0};
 struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_request desired={0};
 int guard,accepted=0;
 if(!s||!off||s->owner||s->active||s->complete||s->busy||s->resume_needed||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||backend.busy||
    backend.owner!=getpid()||off->request.enabled!=0||!off->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(backend.phase==WR_IOT_OWNER_OFF){
  if(!wr_iot_rc_backend_closed(&closed))goto done;
  memset(&s->desired,0,sizeof(s->desired));
  s->owner=getpid();s->complete=1;
  memcpy(s->id,backend.stop.id,sizeof(s->id));s->created=backend.stop.created;
  accepted=1;goto done;
 }
 if(backend.phase!=WR_IOT_OWNER_ACTIVE)goto done;
 memcpy(observed.id,backend.start.input.id,sizeof(observed.id));
 observed.created=backend.start.input.created;observed.state=WR_IOT_RESULT_APPLIED;
 if(!wr_iot_activation_owner_observed(&backend,&observed))goto done;
 /* Snapshot before OFF can clear the runner's original request. This is the
  * desired configuration for later explicit resume, not a startup baseline
  * to restore while the driver/network are still uncertain. */
 desired=backend.start.input.request;
 (void)wr_iot_activation_owner_execute(&backend,off,0,0,0);
 if(backend.phase!=WR_IOT_OWNER_STOP)goto done;
 s->owner=getpid();s->active=1;s->resume_needed=1;s->desired=desired;
 memcpy(s->id,backend.stop.id,sizeof(s->id));s->created=backend.stop.created;
 accepted=1;
 done:memset(&desired,0,sizeof(desired));wr_iot_service_guard_leave(guard);return accepted;
}
int wr_iot_rc_quiesce_advance(struct wr_iot_rc_quiesce *s,
 struct wr_iot_driver_closed_result *out)
{
 int guard,ok=0;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!s||s->owner!=getpid()||s->busy||!wr_iot_rc_shutdown.active||
    backend.owner!=getpid()||backend.busy||!s->created||
    !memchr(s->id,0,sizeof(s->id))||!wr_iot_control_id(s->id))return 0;
 if((!s->active&&!s->complete)||strcmp(s->id,backend.stop.id)||s->created!=backend.stop.created)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 s->busy=1;
 if(s->active)(void)wr_iot_activation_owner_continue(&backend,s->id,s->created);
 if(backend.phase==WR_IOT_OWNER_OFF&&wr_iot_rc_backend_closed(out)){
  s->active=0;s->complete=1;ok=1;
 }
 s->busy=0;wr_iot_service_guard_leave(guard);return ok;
}
