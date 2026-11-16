/* Compose after the real backend/rebind declarations. No shared owner copies.
 * A retained binding needs explicit terminal detach before public admission. */
#include <net/if.h>
#include "bridge.h"
#include "rc-quiesce.h"
#include "dns-activation.h"
#include "restart-initial-parent.h"
#include "restart-profile.h"
#include "restart-main-bridge.h"
#include "rc-shutdown-admission.h"
#include "restart-initial-handoff.h"
static struct wr_iot_restart_restore *wr_iot_initial_restart_parent;
static struct wr_iot_driver_identity wr_iot_initial_restart_identity;
static int initial_restart_retained(void)
{return wr_iot_initial_restart_parent!=NULL;}
static int initial_restart_request_same(const struct wr_iot_control_request *a,
 const struct wr_iot_control_request *b)
{
 if(!a||!b||!a->created||a->created!=b->created||a->request.enabled!=1||b->request.enabled!=1||
    !memchr(a->id,0,sizeof(a->id))||!memchr(b->id,0,sizeof(b->id))||
    !wr_iot_control_id(a->id)||strcmp(a->id,b->id))return 0;
#define SAME(f) if(!memchr(a->request.f,0,sizeof(a->request.f))||!memchr(b->request.f,0,sizeof(b->request.f))||strcmp(a->request.f,b->request.f))return 0;
 SAME(ssid) SAME(password) SAME(gateway) SAME(mask) SAME(first) SAME(last)
#undef SAME
 return 1;
}
static int initial_restart_parent_request(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 struct wr_iot_control_request expected={0};static const char hex[]="0123456789abcdef";
 unsigned i;int same;volatile unsigned char *wipe;size_t n;
 if(!s||!r||!s->handoff_created)return 0;
 for(i=0;i<16;i++){expected.id[2*i]=hex[s->open_id[i]>>4];expected.id[2*i+1]=hex[s->open_id[i]&15];}
 expected.created=s->handoff_created;expected.request=s->generation.origin.desired;
 same=initial_restart_request_same(r,&expected);
 wipe=(volatile unsigned char*)&expected;n=sizeof(expected);while(n--)*wipe++=0;
 return same;
}
static int initial_restart_bound(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 return s&&r&&wr_iot_initial_restart_parent==s&&s->initial_start_claimed==1&&
  !rebind.owner&&backend.owner==getpid()&&!backend.busy&&
  backend.start.owner==getpid()&&!backend.start.busy&&
  s->main.identity.adapter_epoch==wr_iot_initial_restart_identity.adapter_epoch&&
  s->main.identity.device_generation==wr_iot_initial_restart_identity.device_generation&&
  initial_restart_parent_request(s,r)&&initial_restart_request_same(r,&backend.start.input);
}
int wr_iot_rc_initial_restart_start_begin(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 int guard,claimed=0;
 if(!s||!r||wr_iot_initial_restart_parent||s->initial_start_claimed||
    !initial_restart_parent_request(s,r)||!wr_iot_rc_boot_idle())return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_rc_boot_idle()||!wr_iot_restart_initial_parent_current(s,1))goto done;
 if(backend.phase==WR_IOT_OWNER_INITIAL_OFF&&
    (backend.initial_off.owner!=getpid()||!backend.initial_off.ready||!backend.initial_off.created||
     !memchr(backend.initial_off.id,0,sizeof(backend.initial_off.id))||
     !wr_iot_control_id(backend.initial_off.id)||!strcmp(r->id,backend.initial_off.id)||
     r->created<backend.initial_off.created))goto done;
 /* This is a new initial runner on the verified new Main, not old CLOSE reuse.
  * Begin may retain refusal/uncertainty: publish binding as soon as owner exists. */
 (void)wr_iot_start_runner_begin(&backend.start,r,1,1,0);
 if(!backend.start.owner)goto done;
 wr_iot_initial_restart_parent=s;wr_iot_initial_restart_identity=s->main.identity;
 backend.owner=getpid();backend.phase=backend.start.phase==WR_IOT_RUN_REJECTED?
  WR_IOT_OWNER_REJECTED:WR_IOT_OWNER_START;claimed=1;
 if(backend.start.admission.admitted&&
    (backend.start.admission.idle.epoch!=s->main.identity.adapter_epoch||
     backend.start.admission.idle.generation!=s->main.identity.device_generation)){
  backend.start.phase=WR_IOT_RUN_UNCERTAIN;backend.phase=WR_IOT_OWNER_START;
 }
 done:wr_iot_service_guard_leave(guard);return claimed;
}
int wr_iot_rc_initial_restart_start_progress(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 int guard,progressed=0;
 if(!initial_restart_bound(s,r)||backend.phase!=WR_IOT_OWNER_START||
    !backend.start.admission.admitted||
    backend.start.admission.idle.epoch!=wr_iot_initial_restart_identity.adapter_epoch||
    backend.start.admission.idle.generation!=wr_iot_initial_restart_identity.device_generation)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(initial_restart_bound(s,r)&&wr_iot_restart_initial_parent_current(s,0)){
  (void)wr_iot_activation_owner_continue(&backend,r->id,r->created);progressed=1;
 }
 wr_iot_service_guard_leave(guard);return progressed;
}
/* Cancellation retains the borrowed parent until terminal physical cleanup.
 * The existing runner checks pending before OPEN and owns its rollback. No
 * STAGE/NETWORK have dedicated cancellation transitions and never execute
 * forward staging/network work. COMMIT remains separately unadmitted. */
static int initial_restart_cancel_allowed(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 if(!initial_restart_bound(s,r)||s->owner!=getpid()||s->busy!=1||
    s->phase!=WR_RESTORE_HANDOFF||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    (backend.phase!=WR_IOT_OWNER_START&&
     !(backend.phase==WR_IOT_OWNER_REJECTED&&!backend.start.admission.admitted)))return 0;
 if((backend.start.phase==WR_IOT_RUN_STAGE||backend.start.phase==WR_IOT_RUN_NETWORK)&&
    (backend.start.admission.idle.epoch!=wr_iot_initial_restart_identity.adapter_epoch||
     backend.start.admission.idle.generation!=wr_iot_initial_restart_identity.device_generation))return 0;
 switch(backend.start.phase){
 case WR_IOT_RUN_REJECTED:
  return backend.start.commit.phase==WR_IOT_COMMIT_IDLE&&!backend.start.admission.admitted&&!backend.start.admission.idle.serial;
 case WR_IOT_RUN_UNCERTAIN:
  return backend.start.commit.phase==WR_IOT_COMMIT_DNS_UNCERTAIN||
   (backend.start.commit.phase==WR_IOT_COMMIT_IDLE&&!backend.start.admission.admitted&&!backend.start.admission.idle.serial);
 case WR_IOT_RUN_COMMIT:return backend.start.commit.phase==WR_IOT_COMMIT_IDLE||backend.start.commit.phase==WR_IOT_COMMIT_DNS_COMMITTED;
 case WR_IOT_RUN_STAGE:
 case WR_IOT_RUN_NETWORK:
 case WR_IOT_RUN_OPEN:
 case WR_IOT_RUN_PRE_ROLLBACK:
 case WR_IOT_RUN_CLOSE:
 case WR_IOT_RUN_CLOSED_ROLLBACK:return 1;
 case WR_IOT_RUN_COMMITTED_OFF:return backend.start.commit.phase==WR_IOT_COMMIT_DNS_COMMITTED;
 default:return 0;
 }
}
static int initial_restart_cancel_committed(void)
{
 struct wr_iot_start_runner *a=&backend.start;
 if(a->owner!=getpid()||a->busy||a->prior_closed.valid||a->admission.reopened||
    !a->admission.admitted||!a->admission.staged||!a->admission.mutation_started||
    a->commit.phase!=WR_IOT_COMMIT_DNS_COMMITTED||a->commit.owner!=getpid()||
    !a->commit.open_token||a->open.owner!=getpid()||a->open.phase!=WR_IOT_OPEN_CONFIRMED||
    memcmp(&a->commit.attempt,&a->open.attempt,sizeof(a->open.attempt))||
    a->admission.snapshot.owner!=getpid()||!a->admission.snapshot.active||
    a->admission.snapshot.token!=1||a->admission.snapshot.recovering||a->admission.snapshot.disabling)return 0;
 if(a->phase==WR_IOT_RUN_COMMIT){
  if(wr_iot_dns_activation_recovery_state()!=0)return 0;
  a->phase=WR_IOT_RUN_COMMITTED_OFF;
 }else if(a->phase!=WR_IOT_RUN_COMMITTED_OFF)return 0;
 /* New normal disable owns current settings. Do not run startup restore or
  * repeat DNS commit after the commit boundary has been confirmed. */
 a->busy=1;backend.busy=1;
 if(a->stop.phase==WR_IOT_STOP_IDLE)(void)wr_iot_precreated_stop_begin(&a->stop,&a->open.attempt);
 else if(wr_iot_precreated_stop_step(&a->stop)&&wr_iot_request_snapshot_finish(&a->admission.snapshot)){
  a->phase=WR_IOT_RUN_REJECTED;backend.phase=WR_IOT_OWNER_REJECTED;
 }
 a->busy=0;backend.busy=0;return 1;
}
int wr_iot_rc_initial_restart_cancel_progress(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 int guard,progressed=0;
 if(!initial_restart_cancel_allowed(s,r))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(initial_restart_cancel_allowed(s,r)){
  if((backend.start.phase==WR_IOT_RUN_UNCERTAIN||backend.start.phase==WR_IOT_RUN_REJECTED)&&
     backend.start.commit.phase==WR_IOT_COMMIT_IDLE&&!backend.start.admission.admitted){
   progressed=wr_iot_start_runner_cancel_admission(&backend.start,r->id,r->created,&wr_iot_initial_restart_identity);
   if(progressed)backend.phase=WR_IOT_OWNER_REJECTED;
  }else if(backend.start.commit.phase==WR_IOT_COMMIT_DNS_COMMITTED&&
     (backend.start.phase==WR_IOT_RUN_COMMIT||backend.start.phase==WR_IOT_RUN_COMMITTED_OFF))
   progressed=initial_restart_cancel_committed();
  else if(backend.start.phase==WR_IOT_RUN_STAGE){
   progressed=wr_iot_start_runner_cancel_stage(&backend.start,r->id,r->created);
   if(progressed&&backend.start.phase==WR_IOT_RUN_REJECTED)backend.phase=WR_IOT_OWNER_REJECTED;
  }else if(backend.start.phase==WR_IOT_RUN_NETWORK)
   progressed=wr_iot_start_runner_cancel_network(&backend.start,r->id,r->created);
  else if(backend.start.phase==WR_IOT_RUN_COMMIT)
   progressed=wr_iot_start_runner_cancel_uncommitted(&backend.start,r->id,r->created);
  else if(backend.start.phase==WR_IOT_RUN_UNCERTAIN)
   progressed=wr_iot_start_runner_cancel_uncertain(&backend.start,r->id,r->created);
  else{(void)wr_iot_activation_owner_continue(&backend,r->id,r->created);progressed=1;}
 }
 wr_iot_service_guard_leave(guard);return progressed;
}
/* Terminal proof for the never-OPEN branch. A REJECTED enum alone cannot
 * authorize parent cleanup: rollback, software isolation and a fresh idle
 * observation must all agree on the retained new Main lifetime. */
int wr_iot_rc_initial_restart_preopen_rejected(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 struct wr_iot_idle_result idle={0};unsigned i;int guard,ok=0;
 if(!initial_restart_bound(s,r)||s->owner!=getpid()||s->busy!=1||
    s->phase!=WR_RESTORE_HANDOFF||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    backend.phase!=WR_IOT_OWNER_REJECTED||backend.start.phase!=WR_IOT_RUN_REJECTED||
    backend.start.admission.snapshot.active||backend.start.admission.snapshot.token||
    (!backend.start.admission.admitted&&
     (backend.start.admission.mutation_started||backend.start.admission.staged||backend.start.admission.snapshot.owner))||
    backend.start.admission.idle.epoch!=wr_iot_initial_restart_identity.adapter_epoch||
    backend.start.admission.idle.generation!=wr_iot_initial_restart_identity.device_generation||
    (backend.start.admission.mutation_started&&backend.start.rollback.phase!=WR_IOT_ROLL_DONE)||
    (backend.start.open.phase!=WR_IOT_OPEN_IDLE&&backend.start.open.phase!=WR_IOT_OPEN_NOT_SUBMITTED)||
    backend.start.close.owner||
    backend.start.open.attempt.identity.adapter_epoch||backend.start.open.attempt.identity.device_generation)return 0;
 for(i=0;i<16;i++)if(backend.start.open.attempt.request_id[i])return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=initial_restart_bound(s,r)&&!if_nametoindex("br-iot")&&
  wr_iot_request_disabled_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_driver_initial_idle_read(s->open_id,&idle)&&
  idle.epoch==wr_iot_initial_restart_identity.adapter_epoch&&
  idle.generation==wr_iot_initial_restart_identity.device_generation&&
  idle.serial>backend.start.admission.idle.serial&&
  !if_nametoindex("br-iot")&&wr_iot_request_disabled_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0;
 wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_rc_initial_restart_active_current(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r)
{
 struct wr_iot_control_result observed={0};int guard,ok=0;
 if(!initial_restart_bound(s,r)||backend.phase!=WR_IOT_OWNER_ACTIVE||
    backend.start.phase!=WR_IOT_RUN_ACTIVE||
    backend.start.open.attempt.identity.adapter_epoch!=wr_iot_initial_restart_identity.adapter_epoch||
    backend.start.open.attempt.identity.device_generation!=wr_iot_initial_restart_identity.device_generation)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(initial_restart_bound(s,r)&&wr_iot_restart_initial_parent_current(s,0)){
  memcpy(observed.id,r->id,sizeof(observed.id));observed.created=r->created;observed.state=WR_IOT_RESULT_APPLIED;
  ok=wr_iot_activation_owner_observed(&backend,&observed)&&
   wr_iot_restart_initial_parent_current(s,0);
 }
 wr_iot_service_guard_leave(guard);return ok;
}

int wr_iot_rc_initial_restart_receipt(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *r,struct wr_iot_initial_restart_receipt *out)
{
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!wr_iot_rc_initial_restart_active_current(s,r)||!backend.start.commit.open_token)return 0;
 memcpy(out->id,r->id,sizeof(out->id));out->created=r->created;
 out->identity=wr_iot_initial_restart_identity;out->open_token=backend.start.commit.open_token;
 return 1;
}
int wr_iot_rc_initial_restart_postrelease_current(const struct wr_iot_initial_restart_receipt *r)
{
 struct wr_iot_control_result observed={0};int guard,ok=0;
 if(!r||!r->created||!r->open_token||!r->identity.adapter_epoch||!r->identity.device_generation||
    !memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id)||
    initial_restart_retained()||rebind.owner||wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    backend.owner!=getpid()||backend.busy||backend.phase!=WR_IOT_OWNER_ACTIVE||
    backend.start.owner!=getpid()||backend.start.busy||backend.start.phase!=WR_IOT_RUN_ACTIVE||
    strcmp(r->id,backend.start.input.id)||r->created!=backend.start.input.created||
    r->identity.adapter_epoch!=backend.start.open.attempt.identity.adapter_epoch||
    r->identity.device_generation!=backend.start.open.attempt.identity.device_generation||
    r->open_token!=backend.start.commit.open_token)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 memcpy(observed.id,r->id,sizeof(observed.id));observed.created=r->created;observed.state=WR_IOT_RESULT_APPLIED;
 ok=wr_iot_activation_owner_observed(&backend,&observed)&&
  !initial_restart_retained()&&!wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;
 wr_iot_service_guard_leave(guard);return ok;
}

/* Dedicated normal OFF from this retained ACTIVE owner. Keep generic quiesce
 * excluded: this path neither clears the binding nor grants physical DOWN. */
int wr_iot_rc_initial_restart_shutdown_begin(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *on,const struct wr_iot_control_request *off,
 struct wr_iot_rc_quiesce *q)
{
 struct wr_iot_control_result observed={0};int guard,ok=0;
 if(!initial_restart_bound(s,on)||s->owner!=getpid()||s->busy!=1||
    s->phase!=WR_RESTORE_HANDOFF||s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    backend.phase!=WR_IOT_OWNER_ACTIVE||!off||!q||q->owner||q->active||q->complete||
    q->busy||q->resume_needed||off->request.enabled||!off->created||off->created<on->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id)||!strcmp(on->id,off->id))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!initial_restart_bound(s,on)||!wr_iot_restart_generation_origin_current(&s->generation))goto done;
 memcpy(observed.id,on->id,sizeof(observed.id));observed.created=on->created;observed.state=WR_IOT_RESULT_APPLIED;
 if(!wr_iot_activation_owner_observed(&backend,&observed))goto done;
 (void)wr_iot_activation_owner_execute(&backend,off,0,0,0);
 if(backend.phase!=WR_IOT_OWNER_STOP)goto done;
 q->owner=getpid();q->active=1;q->created=backend.stop.created;
 memcpy(q->id,backend.stop.id,sizeof(q->id));
 /* Shutdown never saves credentials for resume. */
 {volatile unsigned char *p=(volatile unsigned char*)&q->desired;size_t n=sizeof(q->desired);while(n--)*p++=0;}
 ok=1;
 done:wr_iot_service_guard_leave(guard);return ok;
}

static int initial_restart_stop_bound(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *on,const struct wr_iot_rc_quiesce *q)
{
 struct wr_iot_request empty={0};
 /* Normal OFF wipes start.input.request. Bind its retained nonsecret envelope
  * and exact original OPEN attempt, never require those erased credentials. */
 return s&&on&&q&&wr_iot_initial_restart_parent==s&&s->initial_start_claimed==1&&
  s->owner==getpid()&&s->busy==1&&s->phase==WR_RESTORE_HANDOFF&&
  s->generation.origin.origin==WR_PHYSICAL_ORIGIN_INITIAL&&
  s->generation.origin.resume_needed==1&&s->generation.origin.desired.enabled==1&&
  !rebind.owner&&backend.owner==getpid()&&!backend.busy&&
  backend.start.owner==getpid()&&!backend.start.busy&&
  (backend.phase==WR_IOT_OWNER_STOP||backend.phase==WR_IOT_OWNER_OFF)&&
  s->main.identity.adapter_epoch==wr_iot_initial_restart_identity.adapter_epoch&&
  s->main.identity.device_generation==wr_iot_initial_restart_identity.device_generation&&
  initial_restart_parent_request(s,on)&&
  memchr(backend.start.input.id,0,sizeof(backend.start.input.id))&&
  !strcmp(on->id,backend.start.input.id)&&on->created==backend.start.input.created&&
  backend.start.open.attempt.identity.adapter_epoch==wr_iot_initial_restart_identity.adapter_epoch&&
  backend.start.open.attempt.identity.device_generation==wr_iot_initial_restart_identity.device_generation&&
  backend.start.commit.open_token&&
  backend.stop.owner==getpid()&&!backend.stop.busy&&backend.stop.active==&backend.start&&
  q->owner==getpid()&&!q->busy&&!q->resume_needed&&
  ((q->active==1&&!q->complete)||(!q->active&&q->complete==1))&&
  !memcmp(&q->desired,&empty,sizeof(empty))&&q->created==backend.stop.created&&
  memchr(q->id,0,sizeof(q->id))&&!strcmp(q->id,backend.stop.id)&&
  wr_iot_rc_shutdown.active&&
  (wr_iot_rc_shutdown.pending==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.pending==SIGQUIT
#endif
  )&&!wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned;
}
static int initial_restart_closed_result(const struct wr_iot_driver_closed_result *closed)
{
 return closed->adapter_epoch==wr_iot_initial_restart_identity.adapter_epoch&&
  closed->device_generation==wr_iot_initial_restart_identity.device_generation&&
  closed->open_token==backend.start.commit.open_token&&closed->open_token&&
  closed->close_serial&&closed->close_serial==backend.stop.stop.close_serial;
}
int wr_iot_rc_initial_restart_shutdown_progress(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *on,struct wr_iot_rc_quiesce *q,
 struct wr_iot_driver_closed_result *out)
{
 struct wr_iot_driver_closed_result closed={0};int guard,ok=0;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!initial_restart_stop_bound(s,on,q))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(initial_restart_stop_bound(s,on,q)&&wr_iot_restart_generation_origin_current(&s->generation)&&
    wr_iot_rc_quiesce_advance(q,&closed)&&initial_restart_stop_bound(s,on,q)&&
    initial_restart_closed_result(&closed)){*out=closed;ok=1;}
 wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_rc_initial_restart_shutdown_closed(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *on,const struct wr_iot_rc_quiesce *q,
 struct wr_iot_driver_closed_result *out)
{
 struct wr_iot_driver_closed_result closed={0};int guard,ok=0;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!initial_restart_stop_bound(s,on,q)||!q->complete||q->active)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(initial_restart_stop_bound(s,on,q)&&wr_iot_restart_generation_origin_current(&s->generation)&&
    wr_iot_rc_backend_closed(&closed)&&initial_restart_stop_bound(s,on,q)&&
    initial_restart_closed_result(&closed)){*out=closed;ok=1;}
 wr_iot_service_guard_leave(guard);return ok;
}

int wr_iot_rc_initial_restart_rollback_closed(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *on)
{
 struct wr_iot_driver_closed_result closed={0};int guard,ok=0;
 if(!initial_restart_bound(s,on)||s->owner!=getpid()||s->busy!=1||s->phase!=WR_RESTORE_HANDOFF||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    backend.phase!=WR_IOT_OWNER_REJECTED||backend.start.phase!=WR_IOT_RUN_REJECTED||
    (backend.start.commit.phase!=WR_IOT_COMMIT_IDLE&&
     !(backend.start.commit.phase==WR_IOT_COMMIT_DNS_UNCERTAIN&&
       backend.start.rollback.dns_abort_required==1&&backend.start.rollback.dns_abort_confirmed==1))||
    backend.start.rollback.owner!=getpid()||backend.start.rollback.phase!=WR_IOT_ROLL_DONE||
    !backend.start.admission.admitted||!backend.start.admission.mutation_started||!backend.start.admission.staged||
    backend.start.open.owner!=getpid()||
    (backend.start.open.phase!=WR_IOT_OPEN_CONFIRMED&&backend.start.open.phase!=WR_IOT_OPEN_RECOVERY)||
    backend.start.admission.snapshot.active||backend.start.admission.snapshot.token||
    backend.start.close.owner!=getpid()||!backend.start.close.close_serial||
    backend.start.close.close.phase!=WR_IOT_CLOSE_OWNER_RELEASED||
    backend.start.close.close.request.adapter_epoch!=wr_iot_initial_restart_identity.adapter_epoch||
    backend.start.close.close.request.device_generation!=wr_iot_initial_restart_identity.device_generation||
    memcmp(backend.start.close.close.request.open_request_id,backend.start.open.attempt.request_id,16)||
    memcmp(&backend.start.close.attempt,&backend.start.open.attempt,sizeof(backend.start.open.attempt))||
    backend.start.open.attempt.identity.adapter_epoch!=wr_iot_initial_restart_identity.adapter_epoch||
    backend.start.open.attempt.identity.device_generation!=wr_iot_initial_restart_identity.device_generation)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=!if_nametoindex("br-iot")&&wr_iot_request_disabled_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_driver_attempt_closed(&backend.start.open.attempt,&closed)&&
  closed.adapter_epoch==wr_iot_initial_restart_identity.adapter_epoch&&
  closed.device_generation==wr_iot_initial_restart_identity.device_generation&&
  closed.open_token&&closed.open_token==backend.start.close.close.request.open_token&&
  closed.close_serial==backend.start.close.close_serial&&
  !if_nametoindex("br-iot")&&wr_iot_request_disabled_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0;
 wr_iot_service_guard_leave(guard);return ok;
}

int wr_iot_rc_initial_restart_committed_closed(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *on)
{
 struct wr_iot_driver_closed_result closed={0};int guard,ok=0;
 if(!initial_restart_bound(s,on)||s->owner!=getpid()||s->busy!=1||s->phase!=WR_RESTORE_HANDOFF||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    backend.phase!=WR_IOT_OWNER_REJECTED||backend.start.phase!=WR_IOT_RUN_REJECTED||
    backend.start.commit.phase!=WR_IOT_COMMIT_DNS_COMMITTED||
    backend.start.rollback.owner||backend.start.rollback.phase!=WR_IOT_ROLL_BRIDGE_DOWN||
    !backend.start.admission.admitted||!backend.start.admission.mutation_started||!backend.start.admission.staged||
    backend.start.open.owner!=getpid()||
    (backend.start.open.phase!=WR_IOT_OPEN_CONFIRMED&&backend.start.open.phase!=WR_IOT_OPEN_RECOVERY)||
    backend.start.admission.snapshot.active||backend.start.admission.snapshot.token||
    backend.start.stop.owner!=getpid()||backend.start.stop.phase!=WR_IOT_STOP_COMPLETE||backend.start.stop.guard||
    !backend.start.stop.close_serial||backend.start.stop.close.request.open_token!=backend.start.commit.open_token||
    backend.start.stop.close.phase!=WR_IOT_CLOSE_OWNER_RELEASED||
    backend.start.stop.close.request.adapter_epoch!=wr_iot_initial_restart_identity.adapter_epoch||
    backend.start.stop.close.request.device_generation!=wr_iot_initial_restart_identity.device_generation||
    memcmp(backend.start.stop.close.request.open_request_id,backend.start.open.attempt.request_id,16)||
    memcmp(&backend.start.stop.attempt,&backend.start.open.attempt,sizeof(backend.start.open.attempt))||
    backend.start.open.attempt.identity.adapter_epoch!=wr_iot_initial_restart_identity.adapter_epoch||
    backend.start.open.attempt.identity.device_generation!=wr_iot_initial_restart_identity.device_generation)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=!if_nametoindex("br-iot")&&wr_iot_request_disabled_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_driver_attempt_closed(&backend.start.open.attempt,&closed)&&
  closed.adapter_epoch==wr_iot_initial_restart_identity.adapter_epoch&&
  closed.device_generation==wr_iot_initial_restart_identity.device_generation&&
  closed.open_token&&closed.open_token==backend.start.stop.close.request.open_token&&
  closed.close_serial==backend.start.stop.close_serial&&
  !if_nametoindex("br-iot")&&wr_iot_request_disabled_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0;
 wr_iot_service_guard_leave(guard);return ok;
}

/* A refused begin owns no runner and may not manufacture a CLOSE receipt.
 * Re-observe boot-idle and never-opened new Main while the physical root still
 * owns generation/profile/guard; this grants cancellation only, never ON. */
int wr_iot_rc_initial_restart_unclaimed_current(struct wr_iot_restart_restore *s,
 const struct wr_iot_control_request *on)
{
 struct wr_iot_idle_result before={0},after={0};int guard,ok=0;
 if(!s||!on||s->owner!=getpid()||s->busy!=1||s->phase!=WR_RESTORE_HANDOFF||
    s->initial_start_claimed||!s->handoff_created||initial_restart_retained()||
    !initial_restart_parent_request(s,on)||!wr_iot_rc_boot_idle()||
    s->generation.origin.origin!=WR_PHYSICAL_ORIGIN_INITIAL||
    s->generation.origin.resume_needed!=1||s->generation.origin.desired.enabled!=1||
    s->generation.owner!=getpid()||s->generation.busy||s->generation.phase!=WR_RESTART_GEN_VERIFIED||
    !s->generation.main_may_have_started||!s->generation.profile.active||
    s->generation.profile.files.count!=1||s->generation.profile.files.pending||
    s->generation.profile.recovering||s->generation.profile.removing||
    s->main.owner!=getpid()||s->main.busy||s->main.phase!=WR_MAIN_READY||
    s->main.generation!=&s->generation||
    s->main.identity.adapter_epoch<=s->generation.origin.initial.epoch||
    s->main.identity.device_generation!=s->generation.origin.initial.generation||
    !wr_iot_rc_shutdown.active||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 if(!wr_iot_rc_boot_idle()||!wr_iot_restart_generation_origin_current(&s->generation)||
    !wr_iot_generated_matches(&s->generation.profile.files.generated[0],s->generation.profile.files.paths[0])||
    !wr_iot_restart_initial_enabled_profile_current(&s->generation.origin.desired)||
    !wr_iot_restart_main_bridge_current()||!wr_iot_request_disabled_current()||
    if_nametoindex("br-iot")||!wr_iot_bss_is_down()||wr_iot_dns_activation_recovery_state()!=0||
    !wr_iot_driver_initial_idle_read(s->open_id,&before)||!before.serial||
    before.epoch!=s->main.identity.adapter_epoch||before.generation!=s->main.identity.device_generation||
    !wr_iot_driver_initial_idle_read(s->open_id,&after)||after.serial<=before.serial||
    after.epoch!=before.epoch||after.generation!=before.generation)goto done;
 ok=wr_iot_rc_boot_idle()&&wr_iot_restart_generation_origin_current(&s->generation)&&
  wr_iot_request_disabled_current()&&!if_nametoindex("br-iot")&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0;
 done:wr_iot_service_guard_leave(guard);return ok;
}

static int initial_restart_receipt_bound(const struct wr_iot_initial_restart_receipt *r)
{
 return r&&r->created&&r->open_token&&r->identity.adapter_epoch&&r->identity.device_generation&&
  memchr(r->id,0,sizeof(r->id))&&wr_iot_control_id(r->id)&&!initial_restart_retained()&&!rebind.owner&&
  backend.owner==getpid()&&!backend.busy&&backend.start.owner==getpid()&&!backend.start.busy&&
  memchr(backend.start.input.id,0,sizeof(backend.start.input.id))&&!strcmp(r->id,backend.start.input.id)&&
  r->created==backend.start.input.created&&r->open_token==backend.start.commit.open_token&&
  r->identity.adapter_epoch==backend.start.open.attempt.identity.adapter_epoch&&
  r->identity.device_generation==backend.start.open.attempt.identity.device_generation&&
  wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.radio_on_owned&&!wr_iot_rc_shutdown.radio_off_owned&&
  (wr_iot_rc_shutdown.pending==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.pending==SIGQUIT
#endif
  );
}
int wr_iot_rc_initial_restart_postrelease_shutdown_begin(const struct wr_iot_initial_restart_receipt *r,
 const struct wr_iot_control_request *off,struct wr_iot_rc_quiesce *q)
{
 struct wr_iot_control_result on={0};int guard,ok=0;
 if(!initial_restart_receipt_bound(r)||backend.phase!=WR_IOT_OWNER_ACTIVE||!off||!q||
    off->request.enabled||!off->created||off->created<r->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id)||!strcmp(off->id,r->id))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 memcpy(on.id,r->id,sizeof(on.id));on.created=r->created;on.state=WR_IOT_RESULT_APPLIED;
 if(initial_restart_receipt_bound(r)&&wr_iot_activation_owner_observed(&backend,&on))
  ok=wr_iot_rc_quiesce_shutdown_begin(q,off);
 wr_iot_service_guard_leave(guard);return ok;
}
int wr_iot_rc_initial_restart_postrelease_shutdown_closed(const struct wr_iot_initial_restart_receipt *r,
 const struct wr_iot_rc_quiesce *q)
{
 struct wr_iot_driver_closed_result closed={0};struct wr_iot_request empty={0};int guard,ok=0;
 if(!initial_restart_receipt_bound(r)||!q||q->owner!=getpid()||q->busy||q->active||!q->complete||
    q->resume_needed||memcmp(&q->desired,&empty,sizeof(empty))||backend.phase!=WR_IOT_OWNER_OFF||
    !memchr(q->id,0,sizeof(q->id))||strcmp(q->id,backend.stop.id)||q->created!=backend.stop.created)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=initial_restart_receipt_bound(r)&&wr_iot_rc_backend_closed(&closed)&&
  closed.adapter_epoch==r->identity.adapter_epoch&&closed.device_generation==r->identity.device_generation&&
  closed.open_token==r->open_token&&closed.close_serial&&closed.close_serial==backend.stop.stop.close_serial;
 wr_iot_service_guard_leave(guard);return ok;
}
