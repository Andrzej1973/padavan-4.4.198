#define _GNU_SOURCE
#include <unistd.h>
#include "restart-resume.h"
#include "rc-shutdown-admission.h"
/* Explicit process-context retirement after terminal take. Never use memset
 * to recover a live/uncertain controller or to discard another owner's state. */
int wr_iot_restart_resume_retire(struct wr_iot_restart_resume *s)
{
 struct wr_iot_restart_restore *r;unsigned i;
 if(!s||s->owner!=getpid()||s->busy||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    (s->phase!=WR_RESUME_DONE&&s->phase!=WR_RESUME_CANCELLED))return 0;
 r=&s->restore;
 if(r->owner!=getpid()||r->busy||
    r->phase!=(s->phase==WR_RESUME_DONE?WR_RESTORE_FINISHED:WR_RESTORE_CANCELLED)||
    r->generation.phase!=WR_RESTART_GEN_COMMITTED||r->generation.busy||r->generation.profile.active||r->generation.profile.files.count||
    r->multicast.busy||r->multicast.main||r->multicast.guest||
    r->main.busy||r->guest.busy||r->services.busy||r->main.generation||r->guest.main||r->services.main||
    s->shutdown.active||s->shutdown.busy)return 0;
 for(i=0;i<WR_IOT_BUNDLE_MAX;i++)if(r->generation.profile.files.saved[i].data)return 0;
 {volatile unsigned char *p=(volatile unsigned char *)s;size_t n=sizeof(*s);while(n--)*p++=0;}
 return 1;
}
