#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "restart-auth-stop.h"
#include "rc-physical-stop.h"
#include "rc-backend.h"
#include "restart-scheduler.h"
#include "restart-restore.h"
#include "rc-quiesce.h"
#include "physical-stop-session.h"
#include "radio-stop-fence.h"
#include "rc-shutdown-admission.h"
#include "service-guard.h"
#include "precreated-entropy.h"
static struct {
 pid_t owner;
 struct wr_iot_rc_physical_intent intent;
 struct wr_iot_physical_session session;
 struct wr_iot_rc_quiesce quiesce;
 int quiesced;
 struct wr_iot_radio_stop_fence fence;
 unsigned int aux_next;
 unsigned char nonce[16];
 struct wr_iot_auth_stop auth;
 int guard,finishing,result;
} physical;
static int physical_begin(const struct wr_iot_rc_physical_intent *intent,
 const struct wr_iot_control_request *off)
{
 struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_physical_stop_request request={0};unsigned char entropy[32];
 if(!intent||intent->restart>1||intent->radio_on>1||intent->reload>1||
    (!intent->restart&&(intent->radio_on||intent->reload))||physical.owner||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 if(!wr_iot_restart_scheduler_prepare())return 0;
 if(!wr_iot_radio_stop_fence_begin(&physical.fence))return 0;
 physical.owner=getpid();physical.intent=*intent;
 physical.guard=wr_iot_service_guard_enter(1);
 if(physical.guard!=1)goto refuse;
 if(off){
  /* Entropy failure must precede normal OFF admission/mutation. */
  if(wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy))goto refuse;
  if(!wr_iot_rc_quiesce_begin(&physical.quiesce,off))goto refuse;
  memcpy(physical.nonce,entropy,sizeof(physical.nonce));return 1;
 }
 if(!wr_iot_rc_backend_closed(&closed)||
    wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy))goto refuse;
 request.action=WR_STOP_ARM;request.epoch=closed.adapter_epoch;
 request.generation=closed.device_generation;request.open_token=closed.open_token;
 request.closed_serial=closed.close_serial;memcpy(request.nonce,entropy,16);
 if(!wr_iot_physical_stop_request_valid(&request))goto refuse;
 memcpy(physical.nonce,request.nonce,sizeof(physical.nonce));
 return 1;
 refuse:physical.finishing=-1;return 1;
}
int wr_iot_rc_physical_begin(const struct wr_iot_rc_physical_intent *intent)
{return physical_begin(intent,NULL);}
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent *intent,
 const struct wr_iot_control_request *off)
{
 if(!off||off->request.enabled||!off->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id))return 0;
 return physical_begin(intent,off);
}
int wr_iot_rc_physical_pending(void)
{return physical.owner==getpid()&&!physical.result&&
 !(physical.finishing==1&&physical.intent.restart);}
void wr_iot_rc_physical_step(void)
{
 struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_physical_stop_request request={0};
 int guard,result=0;sigset_t queued;
 if(!wr_iot_rc_physical_pending())return;
 if(wr_iot_rc_shutdown.active&&!sigpending(&queued)){
  if(sigismember(&queued,SIGTERM)==1)(void)wr_iot_rc_shutdown_note(SIGTERM);
#ifdef SIGQUIT
  else if(sigismember(&queued,SIGQUIT)==1)(void)wr_iot_rc_shutdown_note(SIGQUIT);
#endif
 }
 if(!physical.finishing&&wr_iot_rc_shutdown.pending&&physical.session.phase==WR_PHYSICAL_SESSION_IDLE&&
    (!physical.quiesce.owner||physical.quiesced)){
  (void)wr_iot_rc_physical_prearm_cancel();return;
 }
 if(!physical.finishing){
  /* Revalidate the retained lock, balancing only this nested guard. Missing
   * admission retains ownership instead of progressing driver operations. */
  if(!wr_iot_rc_shutdown.active||physical.guard!=1)return;
  guard=wr_iot_service_guard_enter(1);if(guard!=1)return;
  if(physical.quiesce.owner&&!physical.quiesced){
   /* One normal-OFF continuation per window; no AUX/Main operations until
    * its exact retained transaction has fresh released CLOSE evidence. */
   if(wr_iot_rc_quiesce_advance(&physical.quiesce,&closed))physical.quiesced=1;
   wr_iot_service_guard_leave(guard);return;
  }
  if(physical.session.phase==WR_PHYSICAL_SESSION_IDLE){
   struct timespec now;unsigned long long ms;
   if(clock_gettime(CLOCK_MONOTONIC,&now)||now.tv_sec<=0){wr_iot_service_guard_leave(guard);return;}
   ms=(unsigned long long)now.tv_sec*1000+(unsigned long long)now.tv_nsec/1000000;
   if(!physical.auth.owner){
    (void)wr_iot_auth_stop_begin(&physical.auth,ms);
    wr_iot_service_guard_leave(guard);return;
   }
   if(!wr_iot_auth_stop_step(&physical.auth,ms)){wr_iot_service_guard_leave(guard);return;}

   if(physical.aux_next<6){
    if(wr_iot_rc_physical_aux_down(physical.aux_next)==1)physical.aux_next++;
   }else if(wr_iot_rc_backend_closed(&closed)){
    /* AUX closure can change driver state. Capture the actual current CLOSE
     * again after all six administrative downs, before creating the ARM. */
    request.action=WR_STOP_ARM;request.epoch=closed.adapter_epoch;
    request.generation=closed.device_generation;request.open_token=closed.open_token;
    request.closed_serial=closed.close_serial;memcpy(request.nonce,physical.nonce,16);
    (void)wr_iot_physical_session_begin(&physical.session,&request);
   }
  }else result=wr_iot_physical_session_advance(&physical.session);
  wr_iot_service_guard_leave(guard);
  if(!result)return;
  physical.finishing=result;
 }
 /* Physical RELEASE is not completion of the captured restart intent.
  * Keep admission and desired-context ownership until a verified restart /
  * fresh-identity resume consumer exists. Never expose an unguarded gap to
  * another control request or queued normal shutdown. No timer releases it. */
 if(physical.finishing==1&&physical.intent.restart)return;
 if(physical.guard==1){wr_iot_service_guard_leave(1);physical.guard=0;}
 /* Clear guards before restoring signals; a pending normal shutdown can run
  * only after exact terminal cleanup. Failed mask restoration retains fence. */
 if(!wr_iot_radio_stop_fence_end(&physical.fence))return;
 physical.result=physical.finishing;
}
int wr_iot_rc_physical_restart_ready(struct wr_iot_rc_physical_intent *intent)
{
 int guard;
 if(!intent||physical.owner!=getpid()||physical.finishing!=1||
    !physical.intent.restart||physical.result||physical.guard!=1||
    !wr_iot_rc_shutdown.active)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 *intent=physical.intent;wr_iot_service_guard_leave(guard);return 1;
}
int wr_iot_rc_physical_take(struct wr_iot_rc_physical_intent *intent)
{
 int result;
 if(!intent||physical.owner!=getpid()||!physical.result)return 0;
 *intent=physical.intent;result=physical.result;
 memset(&physical,0,sizeof(physical));return result;
}

int wr_iot_rc_physical_resume_read(struct wr_iot_rc_physical_resume *out)
{
 struct wr_iot_rc_physical_intent intent={0};
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!wr_iot_rc_physical_restart_ready(&intent)||
    physical.session.owner!=getpid()||physical.session.busy||
    physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE||
    physical.session.request.action!=WR_STOP_QUERY||
    !wr_iot_physical_stop_request_valid(&physical.session.request)||
    (physical.quiesce.owner&&(!physical.quiesced||!physical.quiesce.complete||
     physical.quiesce.active||physical.quiesce.busy||physical.quiesce.owner!=getpid())))return 0;
 /* Session retains QUERY identity; COMPLETE proves the same identity was
  * acknowledged for RELEASE. Reconstruct only that terminal action byte. */
 out->intent=intent;out->physical=physical.session.request;
 out->physical.action=WR_STOP_RELEASE;
 if(physical.quiesce.owner){
  out->resume_needed=physical.quiesce.resume_needed;
  if(out->resume_needed)out->desired=physical.quiesce.desired;
 }
 return 1;
}

static void resume_wipe(void *data,size_t size)
{volatile unsigned char *p=data;while(size--)*p++=0;}
/* Already validated; no setters, restore or fallible observation.
 * Runs under active admission before deferred shutdown delivery. */
static void resume_cleanup(void *context)
{
 struct wr_iot_restart_restore *s=context;
 wr_iot_bundle_release(&s->generation.profile.files);
 resume_wipe(&s->generation.profile,sizeof(s->generation.profile));
 resume_wipe(&s->generation.origin.desired,sizeof(s->generation.origin.desired));
 resume_wipe(&physical.quiesce.desired,sizeof(physical.quiesce.desired));
 s->generation.phase=WR_RESTART_GEN_COMMITTED;
 s->main.generation=NULL;s->guest.main=NULL;s->services.main=NULL;
 s->phase=WR_RESTORE_FINISHED;s->busy=0;
 physical.result=1;
 wr_iot_service_guard_leave(1);physical.guard=0;
}
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore *s)
{
 int finished;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||
    physical.owner!=getpid()||physical.finishing!=1||physical.result||physical.guard!=1||
    !physical.intent.restart||physical.fence.owner!=getpid()||physical.fence.level!=1||
    physical.session.owner!=getpid()||physical.session.busy||
    physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE||
    !wr_iot_restart_restore_finish_check(s))return 0;
 s->busy=1;
 finished=wr_iot_radio_stop_fence_end_cleanup(&physical.fence,resume_cleanup,s);
 if(!finished)s->busy=0;
 return finished;
}

static void resume_cancel_cleanup(void *context)
{
 struct wr_iot_restart_restore *s=context;
 resume_cleanup(s);
 s->phase=WR_RESTORE_CANCELLED;physical.result=-1;
}
int wr_iot_rc_physical_resume_cancel(struct wr_iot_restart_restore *s,const struct wr_iot_rc_quiesce *off)
{
 int cancelled;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_RESTORE_HANDOFF||
    physical.owner!=getpid()||physical.finishing!=1||physical.result||physical.guard!=1||
    !physical.intent.restart||physical.fence.owner!=getpid()||physical.fence.level!=1||
    physical.session.owner!=getpid()||physical.session.busy||physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE||
    !wr_iot_restart_restore_cancel_check(s,off))return 0;
 s->busy=1;
 cancelled=wr_iot_radio_stop_fence_end_cleanup(&physical.fence,resume_cancel_cleanup,s);
 if(!cancelled)s->busy=0;
 return cancelled;
}

int wr_iot_rc_physical_premain_cancel(struct wr_iot_restart_restore *s)
{
 int cancelled;
 if(!s||s->owner!=getpid()||s->busy||
    (s->phase!=WR_RESTORE_PROFILE&&s->phase!=WR_RESTORE_MAIN_START&&s->phase!=WR_RESTORE_RETAINED)||
    s->main.owner||s->guest.owner||s->services.owner||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||physical.owner!=getpid()||physical.finishing!=1||physical.result||physical.guard!=1||
    !physical.intent.restart||physical.fence.owner!=getpid()||physical.fence.level!=1||
    physical.session.owner!=getpid()||physical.session.busy||physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE||
    !wr_iot_restart_generation_rollback_current(&s->generation))return 0;
 s->busy=1;
 cancelled=wr_iot_radio_stop_fence_end_cleanup(&physical.fence,resume_cancel_cleanup,s);
 if(!cancelled)s->busy=0;
 return cancelled;
}

int wr_iot_rc_physical_prehandoff_cancel(struct wr_iot_restart_restore *s)
{
 int cancelled;
 if(!s||s->busy||physical.owner!=getpid()||physical.finishing!=1||physical.result||
    physical.guard!=1||!physical.intent.restart||physical.fence.owner!=getpid()||physical.fence.level!=1||
    physical.session.owner!=getpid()||physical.session.busy||physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE||
    !wr_iot_restart_prehandoff_cancel_check(s))return 0;
 s->busy=1;
 cancelled=wr_iot_radio_stop_fence_end_cleanup(&physical.fence,resume_cancel_cleanup,s);
 if(!cancelled)s->busy=0;
 return cancelled;
}

static void preresume_cancel_cleanup(void *context)
{
 (void)context;
 resume_wipe(&physical.quiesce.desired,sizeof(physical.quiesce.desired));
 physical.result=-1;wr_iot_service_guard_leave(1);physical.guard=0;
}
int wr_iot_rc_physical_preresume_cancel(void)
{
 struct wr_iot_rc_physical_resume observed={0};int valid;
 if(!wr_iot_restart_scheduler_unowned()||!wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||physical.fence.owner!=getpid()||physical.fence.level!=1)return 0;
 valid=wr_iot_rc_physical_resume_read(&observed);
 resume_wipe(&observed,sizeof(observed));
 if(!valid)return 0;
 return wr_iot_radio_stop_fence_end_cleanup(&physical.fence,preresume_cancel_cleanup,NULL);
}

int wr_iot_rc_physical_prearm_cancel(void)
{
 struct wr_iot_driver_closed_result closed={0};int guard,valid;
 if(!wr_iot_restart_scheduler_unowned()||physical.owner!=getpid()||
    physical.finishing||physical.result||physical.guard!=1||
    physical.session.owner||physical.session.busy||physical.session.phase!=WR_PHYSICAL_SESSION_IDLE||
    physical.fence.owner!=getpid()||physical.fence.level!=1||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||(physical.quiesce.owner&&(!physical.quiesced||!physical.quiesce.complete||
      physical.quiesce.active||physical.quiesce.busy||physical.quiesce.owner!=getpid())))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 valid=wr_iot_rc_backend_closed(&closed);
 wr_iot_service_guard_leave(guard);
 if(!valid)return 0;
 /* No ARM/descriptor transition/Main DOWN has been submitted by this owner.
  * Administrative AUX/auth changes need no restart for a normal shutdown. */
 return wr_iot_radio_stop_fence_end_cleanup(&physical.fence,preresume_cancel_cleanup,NULL);
}
