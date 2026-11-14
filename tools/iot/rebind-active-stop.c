#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "rebind-active-stop.h"
#include "rc-shutdown-admission.h"
int wr_iot_rebind_active_stop_begin(struct wr_iot_rebind_active_stop *s,
 struct wr_iot_rebind_runner *active,const struct wr_iot_control_request *request)
{
 if(!s||!active||!request||s->owner||s->active||s->busy||s->complete||
    s->stop.phase!=WR_IOT_STOP_IDLE||!wr_iot_rc_shutdown.active||
    active->owner!=getpid()||active->busy||active->phase!=WR_IOT_RUN_ACTIVE||
    active->commit.phase!=WR_IOT_COMMIT_ACTIVE||request->request.enabled!=0||
    !request->created||!memchr(request->id,0,sizeof(request->id))||
    !wr_iot_control_id(request->id)||
    !memchr(active->input.id,0,sizeof(active->input.id))||
    !strcmp(request->id,active->input.id)||
    request->created<active->input.created)return 0;
 /* Resume detects foreign current settings before any OFF mutation. A failed
  * later step retains this guard and baseline; never reconstruct from disk. */
 if(!wr_iot_request_snapshot_resume(&active->start.admission.snapshot))return 0;
 s->owner=getpid();s->active=active;s->created=request->created;
 memcpy(s->id,request->id,sizeof(s->id));active->phase=WR_IOT_RUN_STOPPING;return 1;
}
enum wr_iot_result_state wr_iot_rebind_active_stop_continue(struct wr_iot_rebind_active_stop *s,
 const char *id,unsigned long long created)
{
 int done=0;
 if(!s||!id||!created||s->owner!=getpid()||s->busy||!s->active||
    !wr_iot_control_id(id)||strcmp(id,s->id)||created!=s->created||
    s->active->owner!=getpid()||s->active->busy||!wr_iot_rc_shutdown.active)
  return WR_IOT_RESULT_RECOVERY;
 if(s->complete)return WR_IOT_RESULT_APPLIED;
 if(s->active->phase!=WR_IOT_RUN_STOPPING||
    !s->active->start.admission.snapshot.active||s->active->start.admission.snapshot.token!=1)
  return WR_IOT_RESULT_RECOVERY;
 s->busy=s->active->busy=1;
 if(s->stop.phase==WR_IOT_STOP_IDLE)
  (void)wr_iot_precreated_stop_begin(&s->stop,&s->active->open.attempt);
 else if(wr_iot_precreated_stop_step(&s->stop)){
  /* Normal OFF has verified CLOSED and removed services/bridge, cleared temp
   * credentials and committed disable. Discard old startup baseline, never
   * restore its gates or overwrite saved configuration. */
  if(wr_iot_request_snapshot_finish(&s->active->start.admission.snapshot)){
   s->complete=done=1;
   /* Original ON can no longer be reported ACTIVE after a completed OFF. */
   s->active->phase=WR_IOT_RUN_STOPPED;
   memset(&s->active->input.request,0,sizeof(s->active->input.request));
  }
 }
 s->busy=s->active->busy=0;
 return done?WR_IOT_RESULT_APPLIED:WR_IOT_RESULT_RECOVERY;
}
