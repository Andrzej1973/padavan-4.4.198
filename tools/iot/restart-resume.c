#define _GNU_SOURCE
#include <unistd.h>
#include "restart-resume.h"
#include "control-channel.h"
#include "rc-shutdown-admission.h"
static void envelope_wipe(void *data,size_t size)
{volatile unsigned char*p=data;while(size--)*p++=0;}
int wr_iot_restart_resume_begin(struct wr_iot_restart_resume*s,const unsigned char*id,unsigned long long created)
{
 int started;
 if(!s||!id||!created||s->owner||s->busy||s->phase!=WR_RESUME_IDLE||
    !wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 s->owner=getpid();s->created=created;s->busy=1;
 started=wr_iot_restart_restore_begin(&s->restore,id);
 s->phase=started?WR_RESUME_RESTORE:WR_RESUME_RETAINED;
 s->busy=0;return started;
}
int wr_iot_restart_resume_step(struct wr_iot_restart_resume*s)
{
 static const char hex[]="0123456789abcdef";
 struct wr_iot_control_request request={0};struct wr_iot_rc_physical_intent intent={0};
 struct wr_iot_driver_closed_result closed={0};
 unsigned i;int done=0;
 if(!s||s->owner!=getpid()||s->busy)return 0;
 if(s->phase==WR_RESUME_DONE)return 1;
 if(s->phase==WR_RESUME_CANCELLED)return -1;
 s->busy=1;
 switch(s->phase){
 case WR_RESUME_RESTORE:
  if(!wr_iot_restart_restore_step(&s->restore))break;
  for(i=0;i<16;i++){request.id[2*i]=hex[s->restore.open_id[i]>>4];request.id[2*i+1]=hex[s->restore.open_id[i]&15];}
  request.created=s->created;request.request=s->restore.generation.origin.desired;
  (void)wr_iot_restart_restore_handoff(&s->restore,&request);
  envelope_wipe(&request,sizeof(request));
  s->phase=s->restore.phase==WR_RESTORE_HANDOFF?WR_RESUME_REBIND:WR_RESUME_RETAINED;
  break;
 case WR_RESUME_REBIND:
  for(i=0;i<16;i++){request.id[2*i]=hex[s->restore.open_id[i]>>4];request.id[2*i+1]=hex[s->restore.open_id[i]&15];}
  /* Existing backend advances its stable owner; never dispatch another begin
   * or publish private resume credentials through the mailbox. */
  (void)wr_iot_activation_continue(request.id,s->created);
  if(wr_iot_restart_restore_rebind_current(&s->restore))s->phase=WR_RESUME_FINISH;
  break;
 case WR_RESUME_SHUTDOWN:
  if(!s->shutdown.owner){
   for(i=0;i<16;i++){request.id[2*i]=hex[s->restore.open_id[i]>>4];request.id[2*i+1]=hex[s->restore.open_id[i]&15];}
   (void)wr_iot_activation_continue(request.id,s->created);
   if(wr_iot_restart_restore_preopen_rejected(&s->restore))s->phase=WR_RESUME_SHUTDOWN_ROLLBACK;
   else (void)wr_iot_rc_quiesce_shutdown_begin(&s->shutdown,&s->stop_input);
   break;
  }
  if(wr_iot_rc_quiesce_advance(&s->shutdown,&closed))s->phase=WR_RESUME_SHUTDOWN_CLOSED;
  break;
 case WR_RESUME_SHUTDOWN_ROLLBACK:
 case WR_RESUME_SHUTDOWN_CLOSED:
  if(s->restore.phase!=WR_RESTORE_CANCELLED){
   (void)wr_iot_restart_guest_step(&s->restore.guest);
   if(!wr_iot_rc_physical_resume_cancel(&s->restore,s->phase==WR_RESUME_SHUTDOWN_ROLLBACK?NULL:&s->shutdown))break;
  }
  if(wr_iot_rc_physical_take(&intent)==-1){s->phase=WR_RESUME_CANCELLED;done=-1;}
  break;
 case WR_RESUME_FINISH:
  if(s->restore.phase!=WR_RESTORE_FINISHED&&!wr_iot_rc_physical_resume_finish(&s->restore))break;
  if(wr_iot_rc_physical_take(&intent)==1){s->phase=WR_RESUME_DONE;done=1;}
  break;
 default:break;
 }
 envelope_wipe(&request,sizeof(request));s->busy=0;return done;
}

int wr_iot_restart_resume_shutdown(struct wr_iot_restart_resume*s,const struct wr_iot_control_request*off)
{
 static const char hex[]="0123456789abcdef";char on_id[33]={0};unsigned i;
 if(!s||!off||s->owner!=getpid()||s->busy||
    (s->phase!=WR_RESUME_REBIND&&s->phase!=WR_RESUME_FINISH)||
    s->restore.phase!=WR_RESTORE_HANDOFF||s->shutdown.owner||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||off->request.enabled!=0||!off->created||off->created<s->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id))return 0;
 for(i=0;i<16;i++){on_id[2*i]=hex[s->restore.open_id[i]>>4];on_id[2*i+1]=hex[s->restore.open_id[i]&15];}
 if(!strcmp(on_id,off->id))return 0;
 /* Store only OFF identity, never arbitrary credentials carried by caller. */
 memcpy(s->stop_input.id,off->id,sizeof(s->stop_input.id));s->stop_input.created=off->created;
 s->phase=WR_RESUME_SHUTDOWN;return 1;
}
