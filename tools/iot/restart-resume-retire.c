#define _GNU_SOURCE
#include <unistd.h>
#include "restart-resume.h"
#include "rc-shutdown-admission.h"
/* Explicit process-context retirement after terminal take. Never use memset
 * to recover a live/uncertain controller or to discard another owner's state. */
static int resume_retire(struct wr_iot_restart_resume *s,int off_admission)
{
 struct wr_iot_restart_restore *r;unsigned i;
 /* Explicit OFF admission or routed shutdown may discard only a fully
  * released unsuccessful tail.
  * This grants no DONE/loaded/file proof: the normal consumer must still
  * observe and close its actual backend before physical shutdown/replay. */
 int discard_released=s&&(off_admission||wr_iot_rc_shutdown.normal_route_requested)&&
  (s->phase==WR_RESUME_WAN||s->phase==WR_RESUME_DONE);
 if(!s||s->owner!=getpid()||s->busy||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    (!discard_released&&s->phase!=WR_RESUME_DONE&&s->phase!=WR_RESUME_CANCELLED))return 0;
 if(s->wan.owner&&(s->wan.owner!=getpid()||
    ((discard_released||s->phase==WR_RESUME_DONE)&&(!s->wan.attempted||!s->wan.returned))))return 0;
 if(!discard_released&&s->phase==WR_RESUME_DONE&&s->led_attempted&&!s->led_returned)return 0;
 if(s->terminal.guard||s->terminal.busy||s->terminal.child||s->terminal.fence.owner||s->terminal.fence.level)return 0;
 r=&s->restore;
 if(r->owner!=getpid()||r->busy||!wr_iot_iapp_child_closed(&r->iapp)||
    r->phase!=((discard_released||s->phase==WR_RESUME_DONE)?WR_RESTORE_FINISHED:WR_RESTORE_CANCELLED)||
    r->generation.phase!=WR_RESTART_GEN_COMMITTED||r->generation.busy||r->generation.profile.active||r->generation.profile.files.count||
    r->multicast.busy||r->multicast.main||r->multicast.guest||
    r->main.busy||r->guest.busy||r->services.busy||r->main.generation||r->guest.main||r->services.main||
    s->shutdown.active||s->shutdown.busy)return 0;
 for(i=0;i<WR_IOT_BUNDLE_MAX;i++)if(r->generation.profile.files.saved[i].data)return 0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!discard_released&&s->phase==WR_RESUME_DONE&&!wr_iot_restart_restore_completed_current(r))return 0;
#endif
 {volatile unsigned char *p=(volatile unsigned char *)s;size_t n=sizeof(*s);while(n--)*p++=0;}
 return 1;
}

int wr_iot_restart_resume_retire(struct wr_iot_restart_resume *s)
{return resume_retire(s,0);}
int wr_iot_restart_resume_retire_for_off(struct wr_iot_restart_resume *s)
{return resume_retire(s,1);}
