#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-shutdown.h"
#include "cold-on-prehandoff.h"
#include "rc-shutdown-admission.h"
static void cold_shutdown_wipe(void *data,size_t n)
{volatile unsigned char *p=data;while(n--)*p++=0;}
static void cold_shutdown_cleanup(void *context)
{
 struct wr_iot_cold_owner *p=context;struct wr_iot_cold_admission *a=&p->admission;
 size_t i;int guard=a->guard;
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  cold_shutdown_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);cold_shutdown_wipe(&a->profile,sizeof(a->profile));
 cold_shutdown_wipe(&p->input,sizeof(p->input));cold_shutdown_wipe(&p->generation,sizeof(p->generation));
 cold_shutdown_wipe(&p->main,sizeof(p->main));cold_shutdown_wipe(&p->guest,sizeof(p->guest));
 cold_shutdown_wipe(&p->services,sizeof(p->services));cold_shutdown_wipe(&p->multicast,sizeof(p->multicast));
 memset(a->nonce,0,sizeof(a->nonce));memset(&a->down,0,sizeof(a->down));
 a->owner=0;a->busy=0;a->guard=0;a->phase=WR_COLD_CANCELLED;
 p->owner=0;p->busy=0;p->reload=0;p->phase=WR_COLD_OWNER_IDLE;
 /* Keep the live a->fence until fence_end clears it after this callback. */
 wr_iot_rc_shutdown.radio_off_owned=0;wr_iot_service_guard_leave(guard);
}
int wr_iot_cold_prehandoff_shutdown(struct wr_iot_cold_owner *p)
{
 if(!p||p->owner!=getpid()||p->busy||p->phase<WR_COLD_OWNER_MAIN_WAIT||p->phase>WR_COLD_OWNER_PREPARED||
    p->main.owner!=getpid()||p->main.busy||p->main.generation!=&p->generation||
    p->generation.owner!=getpid()||p->generation.busy||p->generation.admission!=&p->admission||
    !p->generation.main_may_have_started||p->generation.phase!=WR_COLD_GEN_VERIFIED||
    p->admission.owner!=getpid()||p->admission.busy!=1||p->admission.guard!=1||
    p->admission.fence.owner!=getpid()||p->admission.fence.level!=1||
    !wr_iot_radio_profile_owned(&p->admission.profile)||p->guest.busy||
    (p->guest.owner&&(p->guest.owner!=getpid()||p->guest.main!=&p->main))||
    !wr_iot_rc_shutdown.active||
    !wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||!wr_iot_rc_cold_never_started(p))return 0;
 /* Existing controller under pending shutdown may only drain its own submitted
  * Guest UP. It does not acquire or close a foreign/no-submission interface. */
 if(p->guest.owner)(void)wr_iot_cold_guest_step(&p->guest);
 if(!wr_iot_cold_prehandoff_shutdown_current(p))return 0;
 return wr_iot_radio_stop_fence_end_cleanup(&p->admission.fence,cold_shutdown_cleanup,p);
}
