#define _GNU_SOURCE
#include <string.h>
#include <time.h>
#include "precreated-entropy.h"
#include "restart-scheduler.h"
#include "restart-resume.h"
#include "rc-shutdown-admission.h"
static struct wr_iot_restart_resume resume;
int wr_iot_restart_scheduler_begin(const unsigned char *id,unsigned long long created)
{
 struct wr_iot_rc_physical_intent intent={0};
 if(resume.owner||!id||!created||!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_rc_physical_restart_ready(&intent)||!intent.restart||!intent.radio_on)return 0;
 return wr_iot_restart_resume_begin(&resume,id,created);
}
int wr_iot_restart_scheduler_begin_fresh(void)
{
 struct wr_iot_rc_physical_intent intent={0};struct timespec now;
 unsigned char bytes[32]={0};unsigned i;unsigned nonzero=0;int result=0;
 if(resume.owner||!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !wr_iot_rc_physical_restart_ready(&intent)||!intent.restart||!intent.radio_on)return 0;
 if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
    wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))goto done;
 for(i=0;i<16;i++)nonzero|=bytes[i];
 if(!nonzero)goto done;
 result=wr_iot_restart_scheduler_begin(bytes,(unsigned long long)now.tv_sec);
 done:{volatile unsigned char*p=bytes;for(i=0;i<sizeof(bytes);i++)p[i]=0;}
 return result;
}
int wr_iot_restart_scheduler_pending(void)
{
 return resume.owner&&resume.phase!=WR_RESUME_DONE&&resume.phase!=WR_RESUME_CANCELLED;
}
int wr_iot_restart_scheduler_step(void)
{
 sigset_t queued;unsigned char bytes[32];struct timespec now;
 struct wr_iot_control_request off={0};unsigned i;int admitted;
 static const char hex[]="0123456789abcdef";
 if(!resume.owner)return 0;
 /* The outer physical fence masks normal shutdown signals. Observe them
  * without consuming the kernel pending signal or changing its mask. */
 if(wr_iot_rc_shutdown.active&&!sigpending(&queued)){
  if(sigismember(&queued,SIGTERM)==1)(void)wr_iot_rc_shutdown_note(SIGTERM);
#ifdef SIGQUIT
  else if(sigismember(&queued,SIGQUIT)==1)(void)wr_iot_rc_shutdown_note(SIGQUIT);
#endif
 }
 if(wr_iot_rc_shutdown.pending&&resume.restore.phase==WR_RESTORE_HANDOFF&&
    (resume.phase==WR_RESUME_REBIND||resume.phase==WR_RESUME_FINISH)){
  /* Failure retains the owned transaction; never progress ON after shutdown.
   * Generate OFF identity only in process context, before any OFF mutation. */
  if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0||
     (unsigned long long)now.tv_sec<resume.created||
     wr_iot_precreated_entropy(NULL,bytes,sizeof(bytes))!=(int)sizeof(bytes))return 0;
  for(i=0;i<16;i++){off.id[2*i]=hex[bytes[i]>>4];off.id[2*i+1]=hex[bytes[i]&15];}
  off.created=(unsigned long long)now.tv_sec;
  admitted=wr_iot_restart_resume_shutdown(&resume,&off);
  {volatile unsigned char*p=bytes;for(i=0;i<sizeof(bytes);i++)p[i]=0;}
  if(!admitted)return 0;
 }
 return wr_iot_restart_resume_step(&resume);
}
int wr_iot_restart_scheduler_shutdown(const char *id,unsigned long long created)
{
 struct wr_iot_control_request off={0};
 if(!id||strnlen(id,sizeof(off.id))!=32||!wr_iot_control_id(id)||!created)return 0;
 memcpy(off.id,id,sizeof(off.id));off.created=created;
 return wr_iot_restart_resume_shutdown(&resume,&off);
}
int wr_iot_restart_scheduler_retire(void)
{return wr_iot_restart_resume_retire(&resume);}
