#define _GNU_SOURCE
#include <string.h>
#include <unistd.h>
#include <time.h>
#include "restart-auth-stop.h"
#include "rc-physical-stop.h"
#include "rc-normal-shutdown.h"
#include "rc-initial-stop.h"
#include "restart-initial-handoff.h"
#include "initial-shutdown-owner.h"
#include "initial-restart-select.h"
#include "radio-stop-contract.h"
#include "rc-backend.h"
#include "profile-history.h"
#include "restart-profile-history.h"
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
 struct wr_iot_rc_initial_stop initial;
 struct wr_iot_initial_shutdown_owner initial_shutdown;
 struct wr_iot_request initial_desired;
 int initial_saved;
 struct wr_iot_rc_quiesce quiesce;
 int quiesced;
 int routed_shutdown;
 int shutdown_release_mask_set;
 sigset_t shutdown_release_mask;
 char stop_id[33];unsigned long long stop_created;
 struct wr_iot_radio_stop_fence fence;
 unsigned int aux_next;
 unsigned char nonce[16];
 struct wr_iot_auth_stop auth;
 int guard,finishing,result;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 struct wr_iot_restart_profile_history finish_profile;
#endif
} physical;
static int physical_begin(const struct wr_iot_rc_physical_intent *intent,
 const struct wr_iot_control_request *off,int routed)
{
 struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_physical_stop_request request={0};unsigned char entropy[32];
 if(!intent||intent->restart>1||intent->radio_on>1||intent->reload>1||
    (!intent->restart&&(intent->radio_on||intent->reload))||physical.owner||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 if(!wr_iot_restart_scheduler_prepare(!intent->restart&&!intent->radio_on))return 0;
 if(routed?!wr_iot_radio_stop_fence_begin_routed_shutdown(&physical.fence):
           !wr_iot_radio_stop_fence_begin(&physical.fence))return 0;
 physical.owner=getpid();physical.intent=*intent;physical.routed_shutdown=routed;
 if(off){memcpy(physical.stop_id,off->id,sizeof(physical.stop_id));physical.stop_created=off->created;}
 physical.guard=wr_iot_service_guard_enter(1);
 if(physical.guard!=1)goto refuse;
 if(off){
  /* Entropy failure must precede normal OFF admission/mutation. */
  if(wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy))goto refuse;
  if(routed&&wr_iot_rc_boot_idle()){
   if(!wr_iot_initial_shutdown_claim(&physical.initial_shutdown,&physical.fence)||
      !wr_iot_rc_backend_initial_shutdown_prepare(off,&physical.initial_shutdown)||
      !wr_iot_rc_initial_stop_begin_shutdown(&physical.initial,entropy,&physical.initial_shutdown))goto refuse;
   memcpy(physical.nonce,entropy,sizeof(physical.nonce));return 1;
  }
  if(routed?!wr_iot_rc_quiesce_shutdown_begin(&physical.quiesce,off):
             !wr_iot_rc_quiesce_begin(&physical.quiesce,off))goto refuse;
  memcpy(physical.nonce,entropy,sizeof(physical.nonce));return 1;
 }
 if(!wr_iot_rc_backend_closed(&closed)){
  /* Missing CLOSE alone is never permission. Admit the distinct initial
   * origin only through fresh complete software/driver initial observation. */
  if(wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy)||
     !wr_iot_activation_prepare_radio_stop()||
     !wr_iot_rc_initial_stop_begin(&physical.initial,entropy)){
   memset(entropy,0,sizeof(entropy));goto refuse;
  }
  memset(entropy,0,sizeof(entropy));return 1;
 }
 if(wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy))goto refuse;
 request.action=WR_STOP_ARM;request.epoch=closed.adapter_epoch;
 request.generation=closed.device_generation;request.open_token=closed.open_token;
 request.closed_serial=closed.close_serial;memcpy(request.nonce,entropy,16);
 if(!wr_iot_physical_stop_request_valid(&request))goto refuse;
 memcpy(physical.nonce,request.nonce,sizeof(physical.nonce));
 return 1;
 refuse:physical.finishing=-1;return 1;
}
/* Explicit initial-origin entry. Existing CLOSED entry stays separate until
 * tagged resume/OFF consumers are integrated. No live owner replacement. */
int wr_iot_rc_physical_begin_initial(const struct wr_iot_rc_physical_intent *intent)
{
 unsigned char entropy[32];
 if(!intent||intent->restart>1||intent->radio_on>1||intent->reload>1||
    (!intent->restart&&(intent->radio_on||intent->reload))||physical.owner||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 if(!wr_iot_restart_scheduler_prepare(!intent->restart&&!intent->radio_on))return 0;
 if(!wr_iot_radio_stop_fence_begin(&physical.fence))return 0;
 physical.owner=getpid();physical.intent=*intent;
 physical.guard=wr_iot_service_guard_enter(1);
 if(physical.guard!=1)goto initial_refuse;
 if(wr_iot_precreated_entropy(NULL,entropy,sizeof(entropy))!=(int)sizeof(entropy)||
    !wr_iot_activation_prepare_radio_stop()||
    !wr_iot_rc_initial_stop_begin(&physical.initial,entropy))goto initial_refuse;
 memset(entropy,0,sizeof(entropy));return 1;
 initial_refuse:memset(entropy,0,sizeof(entropy));physical.finishing=-1;return 1;
}
/* Candidate saved-policy entry: retains owner on read refusal, before any
 * scheduler step can submit ARM or Main DOWN. Restore has separate gates. */
int wr_iot_rc_physical_begin_initial_saved(const struct wr_iot_rc_physical_intent *intent)
{
 struct wr_iot_request desired={0};volatile unsigned char *wipe;size_t n;
 if(!intent||intent->restart!=1||intent->radio_on!=1)return 0;
 if(!wr_iot_rc_physical_begin_initial(intent))return 0;
 if(!physical.finishing){
  if(!wr_iot_rc_shutdown.pending&&wr_iot_rc_radio_on_saved_request(&desired)&&
     !wr_iot_rc_shutdown.pending){physical.initial_desired=desired;physical.initial_saved=1;}
  else physical.finishing=-1;
 }
 wipe=(volatile unsigned char*)&desired;n=sizeof(desired);while(n--)*wipe++=0;
 return 1;
}
/* Selected entry owns refusal cleanup after any physical claim. It cannot
 * authorize fallback merely because a later lifetime observation failed. */
int wr_iot_rc_physical_begin_initial_selected(const struct wr_iot_rc_physical_intent *intent,
 const unsigned char *nonce,const struct wr_iot_idle_result *selected)
{
 unsigned i,nonzero=0;
 if(!nonce||!selected||!selected->epoch||!selected->generation||!selected->serial)return 0;
 for(i=0;i<16;i++)nonzero|=nonce[i];
 if(!nonzero||!wr_iot_rc_physical_begin_initial_saved(intent))return 0;
 if(!physical.finishing&&
    (!physical.initial_saved||physical.initial.session.owner||physical.initial.session.busy||
     physical.initial.session.phase!=WR_INITIAL_PHYSICAL_SESSION_IDLE||
     !wr_iot_initial_restart_selected_current(nonce,selected)))physical.finishing=-1;
 return 1;
}
int wr_iot_rc_physical_begin_initial_off(const struct wr_iot_control_request *off)
{
 const struct wr_iot_rc_physical_intent intent={0,0,0};
 if(!off||off->request.enabled||!off->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id))return 0;
 if(!wr_iot_rc_physical_begin_initial(&intent))return 0;
 memcpy(physical.stop_id,off->id,sizeof(physical.stop_id));physical.stop_created=off->created;
 return 1;
}
int wr_iot_rc_physical_initial_off_read(const char *id,unsigned long long created,
 struct wr_iot_physical_initial_request *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!id||strnlen(id,sizeof(physical.stop_id))!=32||!created||
    physical.owner!=getpid()||physical.intent.restart||physical.intent.radio_on||
    physical.intent.reload||physical.stop_created!=created||
    memcmp(physical.stop_id,id,sizeof(physical.stop_id))||physical.result!=1||
    physical.finishing!=1||physical.guard||physical.fence.owner)return 0;
 return wr_iot_rc_initial_stop_released(&physical.initial,out);
}
int wr_iot_rc_physical_initial_release_read(struct wr_iot_physical_initial_request *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(physical.owner!=getpid()||physical.finishing!=1||physical.guard!=1||
    !physical.intent.restart||!wr_iot_rc_shutdown.active)return 0;
 return wr_iot_rc_initial_stop_released(&physical.initial,out);
}
int wr_iot_rc_physical_begin(const struct wr_iot_rc_physical_intent *intent)
{return physical_begin(intent,NULL,0);}
int wr_iot_rc_physical_begin_quiesce(const struct wr_iot_rc_physical_intent *intent,
 const struct wr_iot_control_request *off)
{
 if(!off||off->request.enabled||!off->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id))return 0;
 return physical_begin(intent,off,0);
}
int wr_iot_rc_physical_begin_routed_shutdown(const struct wr_iot_control_request *off)
{
 const struct wr_iot_rc_physical_intent intent={0,0,0};
 if(!off||off->request.enabled||!off->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id))return 0;
 return physical_begin(&intent,off,1);
}
int wr_iot_rc_physical_pending(void)
{return physical.owner==getpid()&&!physical.result&&
 !(physical.finishing==1&&physical.intent.restart);}
/* Infallible terminal publication before deferred shutdown replay. Keep the
 * intent/session receipt until the exact terminal consumer takes it. */
static void physical_stop_cleanup(void *context)
{
 volatile unsigned char *p=(volatile unsigned char *)&physical.quiesce.desired;
 size_t n=sizeof(physical.quiesce.desired);
 (void)context;
 while(n--)*p++=0;
 p=(volatile unsigned char *)&physical.initial_desired;n=sizeof(physical.initial_desired);while(n--)*p++=0;physical.initial_saved=0;
 physical.result=physical.finishing;
 if(physical.guard==1){wr_iot_service_guard_leave(1);physical.guard=0;}
}
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
 if(!physical.routed_shutdown&&!physical.finishing&&wr_iot_rc_shutdown.pending&&physical.session.phase==WR_PHYSICAL_SESSION_IDLE&&
    (!physical.quiesce.owner||physical.quiesced)){
  (void)wr_iot_rc_physical_prearm_cancel();return;
 }
 if(!physical.finishing){
  /* Revalidate the retained lock, balancing only this nested guard. Missing
   * admission retains ownership instead of progressing driver operations. */
  if(!wr_iot_rc_shutdown.active||physical.guard!=1)return;
  guard=wr_iot_service_guard_enter(1);if(guard!=1)return;
  if(physical.initial.owner){
   result=wr_iot_rc_initial_stop_step(&physical.initial);
   wr_iot_service_guard_leave(guard);
   if(!result)return;
   physical.finishing=result;goto initial_finish;
  }
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
 initial_finish:
 /* Physical RELEASE is not completion of the captured restart intent.
  * Keep admission and desired-context ownership until a verified restart /
  * fresh-identity resume consumer exists. Never expose an unguarded gap to
  * another control request or queued normal shutdown. No timer releases it. */
 if(physical.finishing==1&&physical.intent.restart)return;
 /* Publish and wipe before deferred signals. Failed mask restoration keeps
  * the guard, desired context and unpublished result for the same owner. */
 if(!wr_iot_radio_stop_fence_end_cleanup(&physical.fence,physical_stop_cleanup,NULL))return;
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
 if(!intent||physical.routed_shutdown||physical.owner!=getpid()||!physical.result)return 0;
 *intent=physical.intent;result=physical.result;
 memset(&physical,0,sizeof(physical));return result;
}

int wr_iot_rc_physical_off_failed(const char *id,unsigned long long created)
{
 return id&&strnlen(id,sizeof(physical.stop_id))==32&&created&&
  physical.owner==getpid()&&!physical.intent.restart&&!physical.intent.radio_on&&
  !physical.intent.reload&&physical.stop_created==created&&
  !memcmp(physical.stop_id,id,sizeof(physical.stop_id))&&
  (physical.finishing==-1||physical.result==-1);
}
int wr_iot_rc_physical_off_read(const char *id,unsigned long long created,
 struct wr_iot_physical_stop_request *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!id||strnlen(id,sizeof(physical.stop_id))!=32||!created||
    physical.owner!=getpid()||physical.intent.restart||physical.intent.radio_on||
    physical.intent.reload||physical.stop_created!=created||
    memcmp(physical.stop_id,id,sizeof(physical.stop_id))||physical.result!=1||
    physical.finishing!=1||physical.guard||physical.fence.owner||
    physical.session.owner!=getpid()||physical.session.busy||
    physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE||
    physical.session.request.action!=WR_STOP_QUERY||
    !wr_iot_physical_stop_request_valid(&physical.session.request)||
    !physical.quiesced||physical.quiesce.owner!=getpid()||
    !physical.quiesce.complete||physical.quiesce.active||physical.quiesce.busy)return 0;
 *out=physical.session.request;out->action=WR_STOP_RELEASE;return 1;
}
int wr_iot_rc_physical_off_profile(const char *id,unsigned long long created,
 const struct wr_iot_physical_stop_request *expected,struct wr_iot_profile_binding *binding,
 struct wr_iot_restart_profile_receipt *profile)
{
 if(!binding||!profile)return 0;
 memset(binding,0,sizeof(*binding));memset(profile,0,sizeof(*profile));
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 {
  struct wr_iot_physical_stop_request released={0};unsigned char a[64],b[64];int guard,ok;
  const struct wr_iot_profile_binding *history=&physical.quiesce.profile_binding;
  if(!wr_iot_rc_physical_off_read(id,created,&released)||
     !wr_iot_physical_stop_request_encode(a,sizeof(a),expected)||
     !wr_iot_physical_stop_request_encode(b,sizeof(b),&released)||memcmp(a,b,sizeof(a))||
     (history->kind!=WR_PROFILE_BACKEND_ACTIVE&&history->kind!=WR_PROFILE_BACKEND_REBIND_ACTIVE)||
     !history->created||!memchr(history->id,0,sizeof(history->id))||!wr_iot_control_id(history->id)||
     history->identity.adapter_epoch!=released.epoch||history->identity.device_generation!=released.generation)return 0;
  guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
  ok=physical.quiesce.profile_receipt.file.existed==1&&
   physical.quiesce.profile_receipt.file.metadata.st_size>0&&
   wr_iot_restart_profile_receipt_current(&physical.quiesce.profile_receipt)&&
   wr_iot_rc_physical_off_read(id,created,&released)&&
   wr_iot_physical_stop_request_encode(b,sizeof(b),&released)&&!memcmp(a,b,sizeof(a));
  if(ok){*binding=*history;*profile=physical.quiesce.profile_receipt;}
  wr_iot_service_guard_leave(guard);return ok;
 }
#else
 (void)id;(void)created;(void)expected;return 0;
#endif
}
/* Final process-context handoff. Restore the mask while routing is still
 * armed, so failed unmask or a newly delivered signal cannot lose the owner.
 * All fallible validation precedes retirement; no driver work is replayed. */
int wr_iot_rc_physical_shutdown_release_cleanup(const char *id,unsigned long long created,
 void (*cleanup)(void *),void *context)
{
 struct wr_iot_physical_stop_request released={0};
 struct wr_iot_physical_initial_request initial_released={0};
 sigset_t blocked;int original;
 if(!physical.routed_shutdown||physical.owner!=getpid())return 0;
 sigemptyset(&blocked);sigaddset(&blocked,SIGTERM);
#ifdef SIGQUIT
 sigaddset(&blocked,SIGQUIT);
#endif
 if(!physical.shutdown_release_mask_set){
  if(sigprocmask(SIG_BLOCK,&blocked,&physical.shutdown_release_mask))return 0;
  physical.shutdown_release_mask_set=1;
 }else if(sigprocmask(SIG_BLOCK,&blocked,NULL))return 0;
 original=wr_iot_rc_shutdown.normal_route_requested;
 if(!physical.routed_shutdown||!wr_iot_rc_shutdown.normal_route_armed||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    (original!=SIGTERM
#ifdef SIGQUIT
     &&original!=SIGQUIT
#endif
    )||!(physical.initial.owner?
      wr_iot_rc_physical_initial_off_read(id,created,&initial_released):
      wr_iot_rc_physical_off_read(id,created,&released))){
  if(!sigprocmask(SIG_SETMASK,&physical.shutdown_release_mask,NULL))
   physical.shutdown_release_mask_set=0;
  return 0;
 }
 /* Do not clear routing while a caller's original mask blocks shutdown:
  * a deferred stock replay must not masquerade as synchronous completion. */
 if(sigismember(&physical.shutdown_release_mask,SIGTERM)==1
#ifdef SIGQUIT
    ||sigismember(&physical.shutdown_release_mask,SIGQUIT)==1
#endif
   ){
  if(!sigprocmask(SIG_SETMASK,&physical.shutdown_release_mask,NULL))
   physical.shutdown_release_mask_set=0;
  return 0;
 }
 if(sigprocmask(SIG_SETMASK,&physical.shutdown_release_mask,NULL))return 0;
 /* PID1 is the only process-context writer. Signals still route until all
  * private state is retired; once disarmed, stock shutdown may run safely. */
 memset(&physical,0,sizeof(physical));
 if(cleanup)cleanup(context);
 /* Publish a closed replay gate before clearing either routing field.
  * Signals at clear/disarm are swallowed until private retirement is final. */
 wr_iot_rc_shutdown.replay_signal=original;
 wr_iot_rc_shutdown.normal_route_requested=0;
 wr_iot_rc_shutdown.normal_route_armed=0;
 wr_iot_rc_shutdown.replay_ready=1;
 (void)wr_iot_rc_shutdown_replay_step();
 return 1;
}
int wr_iot_rc_physical_shutdown_release(const char *id,unsigned long long created)
{return wr_iot_rc_physical_shutdown_release_cleanup(id,created,NULL,NULL);}
int wr_iot_rc_physical_take_off(const char *id,unsigned long long created)
{
 struct wr_iot_rc_physical_intent intent={0};
 if(!id||strnlen(id,sizeof(physical.stop_id))!=32||!created||
    physical.owner!=getpid()||physical.intent.restart||physical.intent.radio_on||
    physical.intent.reload||physical.stop_created!=created||
    memcmp(physical.stop_id,id,sizeof(physical.stop_id)))return 0;
 return wr_iot_rc_physical_take(&intent);
}

int wr_iot_rc_physical_resume_read(struct wr_iot_rc_physical_resume *out)
{
 struct wr_iot_rc_physical_intent intent={0};
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!wr_iot_rc_physical_restart_ready(&intent))return 0;
 if(physical.initial.owner){
  if(!wr_iot_rc_physical_initial_release_read(&out->initial))return 0;
  out->origin=WR_PHYSICAL_ORIGIN_INITIAL;out->intent=intent;
  if(physical.initial_saved){
   out->desired=physical.initial_desired;out->resume_needed=out->desired.enabled;
  }
  /* Desired saved policy is separate from an old active OPEN/CLOSE context. */
  return 1;
 }
 if(physical.session.owner!=getpid()||physical.session.busy||
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
 if(s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL&&s->generation.origin.desired.enabled)
  wr_iot_rc_initial_restart_detach_commit();
 wr_iot_bundle_release(&s->generation.profile.files);
 resume_wipe(&s->generation.profile,sizeof(s->generation.profile));
 resume_wipe(&s->generation.origin.desired,sizeof(s->generation.origin.desired));
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 /* Every generator borrow ended synchronously before finish/cancel preflight.
  * Retain no canonical credential record after terminal cleanup. */
 resume_wipe(&s->generation.config_revision,sizeof(s->generation.config_revision));
 resume_wipe(&s->generation.provisioning,sizeof(s->generation.provisioning));
#endif
 resume_wipe(&physical.quiesce.desired,sizeof(physical.quiesce.desired));
 resume_wipe(&physical.initial_desired,sizeof(physical.initial_desired));physical.initial_saved=0;
 s->generation.phase=WR_RESTART_GEN_COMMITTED;
 s->main.generation=NULL;s->guest.main=NULL;s->services.main=NULL;
 s->multicast.main=NULL;s->multicast.guest=NULL;
 s->phase=WR_RESTORE_FINISHED;s->busy=0;
 physical.result=1;
 wr_iot_service_guard_leave(1);physical.guard=0;
}
/* Separate successful callback: shared cancellation cleanup never publishes
 * the preflight candidate. Failed unmask leaves it inert in physical owner. */
static void resume_success_cleanup(void *context)
{
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 ((struct wr_iot_restart_restore *)context)->completion=physical.finish_profile;
 wr_iot_rc_restart_profile_commit(&physical.finish_profile);
 memset(&physical.finish_profile,0,sizeof(physical.finish_profile));
#endif
 resume_cleanup(context);
}
int wr_iot_rc_physical_resume_finish(struct wr_iot_restart_restore *s)
{
 int finished;
 if(!s||s->owner!=getpid()||s->busy||s->multicast.busy||!wr_iot_iapp_child_closed(&s->iapp)||(s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?
      s->phase!=(s->generation.origin.desired.enabled?WR_RESTORE_HANDOFF:WR_RESTORE_PREPARED):s->phase!=WR_RESTORE_HANDOFF)||
    physical.owner!=getpid()||physical.finishing!=1||physical.result||physical.guard!=1||
    !physical.intent.restart||physical.fence.owner!=getpid()||physical.fence.level!=1||
    (s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?
      (physical.initial.session.owner!=getpid()||physical.initial.busy||
       physical.initial.result!=1||physical.initial.session.busy||
       physical.initial.session.phase!=WR_INITIAL_PHYSICAL_SESSION_COMPLETE):
      (physical.session.owner!=getpid()||physical.session.busy||
       physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE))||
    !wr_iot_restart_restore_finish_check(s))return 0;
 if(s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL&&
    s->generation.origin.desired.enabled&&!wr_iot_rc_normal_shutdown_arm_ready())return 0;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 if(!wr_iot_rc_restart_profile_prepare(s,&physical.finish_profile))return 0;
#endif
 s->busy=1;
 finished=wr_iot_radio_stop_fence_end_cleanup_unless_shutdown(&physical.fence,resume_success_cleanup,s);
 if(!finished)s->busy=0;
 return finished;
}

static void resume_cancel_cleanup(void *context)
{
 struct wr_iot_restart_restore *s=context;
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED == 1
 memset(&s->completion,0,sizeof(s->completion));
 memset(&physical.finish_profile,0,sizeof(physical.finish_profile));
#endif
 resume_cleanup(s);
 s->phase=WR_RESTORE_CANCELLED;physical.result=-1;
}
int wr_iot_rc_physical_resume_cancel(struct wr_iot_restart_restore *s,const struct wr_iot_rc_quiesce *off)
{
 int cancelled;
 if(!s||s->owner!=getpid()||s->busy||s->multicast.busy||!wr_iot_iapp_child_closed(&s->iapp)||s->phase!=WR_RESTORE_HANDOFF||
    physical.owner!=getpid()||physical.finishing!=1||physical.result||physical.guard!=1||
    !physical.intent.restart||physical.fence.owner!=getpid()||physical.fence.level!=1||
    (s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL?
      (physical.initial.session.owner!=getpid()||physical.initial.busy||
       physical.initial.result!=1||physical.initial.session.busy||
       physical.initial.session.phase!=WR_INITIAL_PHYSICAL_SESSION_COMPLETE):
      (physical.session.owner!=getpid()||physical.session.busy||
       physical.session.phase!=WR_PHYSICAL_SESSION_COMPLETE))||
    !wr_iot_restart_restore_cancel_check(s,off))return 0;
 s->busy=1;
 cancelled=wr_iot_radio_stop_fence_end_cleanup(&physical.fence,resume_cancel_cleanup,s);
 if(!cancelled)s->busy=0;
 return cancelled;
}

int wr_iot_rc_physical_premain_cancel(struct wr_iot_restart_restore *s)
{
 int cancelled;
 if(!s||s->owner!=getpid()||s->busy||s->multicast.busy||!wr_iot_iapp_child_closed(&s->iapp)||
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
 if(!s||s->busy||s->multicast.busy||!wr_iot_iapp_child_closed(&s->iapp)||physical.owner!=getpid()||physical.finishing!=1||physical.result||
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
 resume_wipe(&physical.initial_desired,sizeof(physical.initial_desired));physical.initial_saved=0;
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
 if(physical.routed_shutdown||!wr_iot_restart_scheduler_unowned()||physical.owner!=getpid()||
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
