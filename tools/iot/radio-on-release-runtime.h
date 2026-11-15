/* Private implementation included ONLY by rc-runtime.c after its receipt.
 * Cleanup uses the same RC-owned receipt storage that preflight inspected. */
#ifndef WR_IOT_RADIO_ON_RELEASE_RUNTIME_H
#define WR_IOT_RADIO_ON_RELEASE_RUNTIME_H
#include "radio-on-release.h"
static struct wr_iot_on_restore *radio_on_releasing;
static int (*radio_on_disabled_observer)(struct wr_iot_on_restore *,void *);
static void *radio_on_disabled_context;
static void rc_on_release_wipe(void *data,size_t length)
{volatile unsigned char *p=data;while(length--)*p++=0;}
static void rc_on_release_cleanup(void *context)
{
 struct wr_iot_on_restore *s=context;struct wr_iot_on_admission *a=s->generation.admission;
 size_t i;
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  rc_on_release_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);rc_on_release_wipe(&a->profile,sizeof(a->profile));
 rc_on_release_wipe(&s->generation.desired,sizeof(s->generation.desired));
 radio_off_receipt_valid=0;rc_on_release_wipe(&radio_off_receipt,sizeof(radio_off_receipt));
 s->generation.phase=WR_ON_GEN_COMMITTED;s->generation.admission=NULL;
 s->main.generation=NULL;s->guest.main=NULL;s->services.guest=NULL;
 s->multicast.main=NULL;s->multicast.guest=NULL;
 a->phase=WR_ON_ADMISSION_RELEASED;a->busy=0;
 wr_iot_rc_shutdown.radio_off_owned=0;s->phase=WR_ON_RESTORE_RELEASED;s->busy=0;radio_on_releasing=NULL;radio_on_disabled_observer=NULL;radio_on_disabled_context=NULL;
 wr_iot_service_guard_leave(a->guard);a->guard=0;
}
static int rc_on_release_capture_profile(struct wr_iot_on_restore *s)
{
 struct wr_iot_restart_profile_receipt r={0};struct wr_iot_radio_profile_state *p=&s->generation.admission->profile;size_t n;
 if(s->profile_receipt.valid)return wr_iot_restart_profile_receipt_current(&s->profile_receipt);
 if(!memchr(p->files.paths[0],0,sizeof(p->files.paths[0])))return 0;
 n=strlen(p->files.paths[0]);if(!n||n>=sizeof(r.path))return 0;
 memcpy(r.path,p->files.paths[0],n+1);r.file=p->files.generated[0];r.owner=getpid();r.valid=1;
 if(!wr_iot_restart_profile_receipt_current(&r))return 0;
 s->profile_receipt=r;return 1;
}
int wr_iot_rc_radio_on_release(struct wr_iot_on_restore *s)
{
 struct wr_iot_on_admission *a;unsigned char expected[64],current[64];
 if(!s||s->owner!=getpid()||s->busy||!s->generation.admission)return 0;
 a=s->generation.admission;
 if(s->phase==WR_ON_RESTORE_RELEASING){
  if(radio_on_releasing!=s||a->owner!=getpid()||a->guard!=1||a->busy!=1||
     a->fence.owner!=getpid()||a->fence.level!=1||a->phase!=WR_ON_ADMISSION_CAPTURED||
     !a->profile.active||!radio_off_receipt_valid||!wr_iot_rc_shutdown.radio_off_owned||
     !wr_iot_physical_stop_request_encode(expected,sizeof(expected),&a->released)||
     !wr_iot_physical_stop_request_encode(current,sizeof(current),&radio_off_receipt)||
     memcmp(expected,current,sizeof(current))||!wr_iot_rc_shutdown.active||
     !wr_iot_restart_profile_receipt_current(&s->profile_receipt))return 0;
 }else{
  if(s->phase!=WR_ON_RESTORE_HANDOFF||radio_on_releasing||!radio_off_receipt_valid)return 0;
  if(!s->wan.owner&&!wr_iot_wan_followup_capture(&s->wan,1))return 0;
  if(!wr_iot_on_release_current(s)||
     !wr_iot_physical_stop_request_encode(expected,sizeof(expected),&a->released)||
     !wr_iot_physical_stop_request_encode(current,sizeof(current),&radio_off_receipt)||
     memcmp(expected,current,sizeof(current))||!rc_on_release_capture_profile(s))return 0;
  radio_on_releasing=s;s->phase=WR_ON_RESTORE_RELEASING;
 }
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&a->fence,rc_on_release_cleanup,s)){s->busy=0;return 0;}
 return s->phase==WR_ON_RESTORE_RELEASED;
}

/* Disabled branch stays PREPARED across unmask failures so every retry can
 * revalidate the complete parent/idle proof without inventing ACTIVE. */
int wr_iot_rc_radio_on_disabled_release(struct wr_iot_on_restore *s,
 int (*observe)(struct wr_iot_on_restore *,void *),void *context)
{
 struct wr_iot_on_admission *a;unsigned char before[64],after[64];
 if(!s||!observe||!context||s->owner!=getpid()||s->busy||
    s->phase!=WR_ON_RESTORE_PREPARED||s->generation.desired.enabled!=0||
    !s->generation.admission||!wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !radio_off_receipt_valid||!wr_iot_rc_shutdown.radio_off_owned||
    (radio_on_releasing&&(radio_on_releasing!=s||radio_on_disabled_observer!=observe||
     radio_on_disabled_context!=context)))return 0;
 a=s->generation.admission;
 if(a->owner!=getpid()||a->busy!=1||a->guard!=1||a->fence.owner!=getpid()||
    a->fence.level!=1||a->phase!=WR_ON_ADMISSION_CAPTURED||
    !wr_iot_physical_stop_request_encode(before,sizeof(before),&a->released)||
    !wr_iot_physical_stop_request_encode(after,sizeof(after),&radio_off_receipt)||
    memcmp(before,after,sizeof(before)))return 0;
 if(!s->wan.owner&&!wr_iot_wan_followup_capture(&s->wan,1))return 0;
 if(!observe(s,context)||!rc_on_release_capture_profile(s)||!observe(s,context))return 0;
 radio_on_releasing=s;radio_on_disabled_observer=observe;radio_on_disabled_context=context;
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&a->fence,rc_on_release_cleanup,s)){s->busy=0;return 0;}
 return s->phase==WR_ON_RESTORE_RELEASED;
}

/* Post-UP shutdown keeps the CURRENT generated profile for stock shutdown.
 * Never restore the pre-UP bytes. Only RC can invalidate its old OFF receipt. */
#include "radio-on-prehandoff.h"
#include "radio-on-shutdown-check.h"
static struct {
 struct wr_iot_on_restore *restore;
 const struct wr_iot_rc_quiesce *off;int posthandoff;
 void (*cleanup)(void *);void *context;
} rc_on_shutdown;
static void rc_on_shutdown_cleanup(void *unused)
{
 struct wr_iot_on_restore *s=rc_on_shutdown.restore;
 struct wr_iot_on_admission *a=s->generation.admission;
 void (*cleanup)(void *)=rc_on_shutdown.cleanup;void *context=rc_on_shutdown.context;
 size_t i;int guard=a->guard;(void)unused;
 for(i=0;i<a->profile.files.count;i++)if(a->profile.files.saved[i].data)
  rc_on_release_wipe(a->profile.files.saved[i].data,a->profile.files.saved[i].size);
 wr_iot_bundle_release(&a->profile.files);rc_on_release_wipe(&a->profile,sizeof(a->profile));
 radio_off_receipt_valid=0;rc_on_release_wipe(&radio_off_receipt,sizeof(radio_off_receipt));
 rc_on_release_wipe(&s->generation.desired,sizeof(s->generation.desired));
 wr_iot_rc_shutdown.radio_off_owned=0;
 a->guard=0;a->busy=0;
 memset(&rc_on_shutdown,0,sizeof(rc_on_shutdown));
 wr_iot_service_guard_leave(guard);
 /* Final root wipe/exclusion release must precede pending signal replay. */
 cleanup(context);
}
static int rc_on_shutdown_release(struct wr_iot_on_restore *s,
 const struct wr_iot_rc_quiesce *off,int posthandoff,void (*cleanup)(void *),void *context)
{
 struct wr_iot_on_admission *a;unsigned char before[64],after[64];
 if(!s||!cleanup||s->owner!=getpid()||s->busy||!s->generation.admission||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    ))return 0;
 a=s->generation.admission;
 if(a->owner!=getpid()||a->guard!=1||a->busy!=1||a->fence.owner!=getpid()||a->fence.level!=1||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_on_owned||
    !wr_iot_rc_shutdown.radio_off_owned||!radio_off_receipt_valid||
    !wr_iot_physical_stop_request_encode(before,sizeof(before),&a->released)||
    !wr_iot_physical_stop_request_encode(after,sizeof(after),&radio_off_receipt)||memcmp(before,after,sizeof(before)))return 0;
 if(posthandoff?!wr_iot_on_shutdown_closed_current(s,off):!wr_iot_on_prehandoff_cancel_current(s))return 0;
 if(rc_on_shutdown.restore){
  if(rc_on_shutdown.restore!=s||rc_on_shutdown.cleanup!=cleanup||rc_on_shutdown.context!=context||rc_on_shutdown.off!=off||rc_on_shutdown.posthandoff!=posthandoff)return 0;
 }else{
  if(radio_on_releasing)return 0;
  rc_on_shutdown.restore=s;rc_on_shutdown.off=off;rc_on_shutdown.posthandoff=posthandoff;rc_on_shutdown.cleanup=cleanup;rc_on_shutdown.context=context;
 }
 s->busy=1;
 if(!wr_iot_radio_stop_fence_end_cleanup(&a->fence,rc_on_shutdown_cleanup,NULL)){s->busy=0;return 0;}
 return 1;
}
int wr_iot_rc_radio_on_shutdown_release(struct wr_iot_on_restore *s,void (*cleanup)(void *),void *context)
{return rc_on_shutdown_release(s,NULL,0,cleanup,context);}
int wr_iot_rc_radio_on_shutdown_closed_release(struct wr_iot_on_restore *s,
 const struct wr_iot_rc_quiesce *off,void (*cleanup)(void *),void *context)
{return rc_on_shutdown_release(s,off,1,cleanup,context);}
#endif
