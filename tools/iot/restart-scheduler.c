#define _GNU_SOURCE
#include <string.h>
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
int wr_iot_restart_scheduler_pending(void)
{
 return resume.owner&&resume.phase!=WR_RESUME_DONE&&resume.phase!=WR_RESUME_CANCELLED;
}
int wr_iot_restart_scheduler_step(void)
{return resume.owner?wr_iot_restart_resume_step(&resume):0;}
int wr_iot_restart_scheduler_shutdown(const char *id,unsigned long long created)
{
 struct wr_iot_control_request off={0};
 if(!id||strnlen(id,sizeof(off.id))!=32||!wr_iot_control_id(id)||!created)return 0;
 memcpy(off.id,id,sizeof(off.id));off.created=created;
 return wr_iot_restart_resume_shutdown(&resume,&off);
}
int wr_iot_restart_scheduler_retire(void)
{return wr_iot_restart_resume_retire(&resume);}
