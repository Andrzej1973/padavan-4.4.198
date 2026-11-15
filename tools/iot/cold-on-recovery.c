#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include "cold-on-recovery.h"
#include "precreated-down-recovery.h"
#include "rc-runtime.h"
#include "rc-backend.h"
#include "rc-shutdown-admission.h"
static int cold_recovery_owned(struct wr_iot_cold_generation *s)
{
 struct wr_iot_cold_admission *a;struct wr_iot_physical_stop_request historical={0};
 struct wr_iot_rc_mode mode={0};
 if(!s||s->owner!=getpid()||s->busy||s->main_may_have_started||!s->admission)return 0;
 a=s->admission;
 return a->owner==getpid()&&a->busy==1&&a->guard==1&&a->phase==WR_COLD_CAPTURED&&
  a->fence.owner==getpid()&&a->fence.level==1&&wr_iot_rc_shutdown.active&&
  wr_iot_rc_shutdown.radio_off_owned&&wr_iot_radio_profile_owned(&a->profile)&&
  a->profile.files.count==1&&!a->profile.removing&&
  !wr_iot_rc_radio_off_receipt(&historical)&&
  wr_iot_rc_radio_on_mode_read(&mode)&&mode.router==1&&mode.radio==1&&mode.mode==0&&
  wr_iot_initial_down_recovery_current(a->nonce,&a->down);
}
int wr_iot_cold_preup_recover(struct wr_iot_cold_generation *s)
{
 int result=0;
 if(!cold_recovery_owned(s)||s->phase<WR_COLD_GEN_CAPTURED||s->phase>WR_COLD_GEN_RESTORED)return 0;
 s->busy=1;s->phase=WR_COLD_GEN_RESTORING;
 if(wr_iot_radio_profile_restore(&s->admission->profile)){
  s->phase=WR_COLD_GEN_RESTORED;result=-1;
 }
 s->busy=0;return result;
}
static void cold_recovery_wipe(void *p,size_t size)
{volatile unsigned char *b=p;while(size--)*b++=0;}
static void cold_recovery_cleanup(void *context)
{
 struct wr_iot_cold_generation *s=context;struct wr_iot_cold_admission *a=s->admission;
 size_t i;
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  cold_recovery_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);
 cold_recovery_wipe(&a->profile,sizeof(a->profile));
 cold_recovery_wipe(&s->desired,sizeof(s->desired));
 cold_recovery_wipe(a->nonce,sizeof(a->nonce));cold_recovery_wipe(&a->down,sizeof(a->down));
 a->busy=0;a->phase=WR_COLD_CANCELLED;s->phase=WR_COLD_GEN_COMMITTED;s->busy=0;
 wr_iot_rc_shutdown.radio_off_owned=0;
 wr_iot_service_guard_leave(a->guard);a->guard=0;
}
int wr_iot_cold_preup_finish(struct wr_iot_cold_generation *s)
{
 struct wr_iot_cold_admission *a;
 if(!cold_recovery_owned(s)||s->phase!=WR_COLD_GEN_RESTORED)return 0;
 a=s->admission;
 if(!a->profile.recovering||!a->profile.recovered||a->profile.files.pending||
    !wr_iot_generated_matches(&a->profile.restored_file,a->profile.files.paths[0])||
    !cold_recovery_owned(s))return 0;
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&a->fence,cold_recovery_cleanup,s)){s->busy=0;return 0;}
 /* No live context survives successful cleanup; deferred signal already had
  * the opportunity to run with all resources released. */
 cold_recovery_wipe(a,sizeof(*a));cold_recovery_wipe(s,sizeof(*s));return 1;
}
