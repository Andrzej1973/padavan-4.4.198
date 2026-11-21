/* RC-private historical disabled ON retirement. Compose after the backend and
 * INITIAL/cold bindings. No borrowed root pointer survives this transfer. */
#include "radio-on-disabled.h"
#include "restart-profile-receipt.h"
/* The shared RC profile history is composed before this fragment. */
static int disabled_retire_stop_resources_empty(const struct wr_iot_precreated_stop *s)
{
 size_t i;
 if(s->guard||s->disable.services.settings.active||s->disable.services.settings.token||
    s->disable.radio.active||s->disable.radio.files.count)return 0;
 for(i=0;i<WR_IOT_BUNDLE_MAX;i++)if(s->disable.radio.files.saved[i].data)return 0;
 return 1;
}
static int disabled_retire_stop_empty(const struct wr_iot_precreated_stop *s)
{
 return s->owner==getpid()&&s->phase==WR_IOT_STOP_COMPLETE&&
  s->close.phase==WR_IOT_CLOSE_OWNER_RELEASED&&disabled_retire_stop_resources_empty(s);
}
/* A normal routed signal may wait for this already completed root. Preserve it
 * through inert transfer/retirement so its consumer can run after exclusion is
 * released. Refusing TERM/QUIT here would deadlock that consumer behind root. */
static int disabled_retire_route_ready(void)
{
 return wr_iot_rc_shutdown.normal_route_armed&&!wr_iot_rc_shutdown.replay_signal&&
  (!wr_iot_rc_shutdown.normal_route_requested||wr_iot_rc_shutdown.normal_route_requested==SIGTERM
#ifdef SIGQUIT
   ||wr_iot_rc_shutdown.normal_route_requested==SIGQUIT
#endif
  );
}
static int disabled_retire_backend_empty(void)
{
 if(!backend.owner)return backend.phase==WR_IOT_OWNER_IDLE&&!backend.busy&&
  !backend.start.owner&&!backend.stop.owner&&!backend.start.stop.owner&&!backend.start.close.owner&&
  !backend.start.rollback.owner&&!backend.start.network.attempted&&
  !backend.start.admission.snapshot.active&&!backend.start.admission.snapshot.token&&
  disabled_retire_stop_resources_empty(&backend.start.stop)&&
  disabled_retire_stop_resources_empty(&backend.stop.stop);
 return backend.owner==getpid()&&!backend.busy&&backend.phase==WR_IOT_OWNER_OFF&&
  backend.start.owner==getpid()&&!backend.start.busy&&backend.start.phase==WR_IOT_RUN_STOPPED&&
  !backend.start.stop.owner&&!backend.start.close.owner&&!backend.start.rollback.owner&&
  disabled_retire_stop_resources_empty(&backend.start.stop)&&
  !backend.start.admission.snapshot.active&&!backend.start.admission.snapshot.token&&
  backend.stop.owner==getpid()&&!backend.stop.busy&&backend.stop.complete&&
  backend.stop.active==&backend.start&&disabled_retire_stop_empty(&backend.stop.stop);
}
static int disabled_retire_old_release(const struct wr_iot_physical_stop_request *p,
 const struct wr_iot_initial_off *next)
{
 const struct wr_iot_precreated_stop *stop;const struct wr_iot_driver_attempt *attempt;
 const char *id;unsigned long long created;
 if(!disabled_retire_backend_empty())return 0;
 if(rebind.owner){
  if(rebind.owner!=getpid()||rebind.busy||rebind.phase!=WR_REBIND_OWNER_OFF||
     rebind.start.owner!=getpid()||rebind.start.busy||rebind.start.phase!=WR_IOT_RUN_STOPPED||
     rebind.start.stop.owner||rebind.start.close.owner||rebind.start.rollback.owner||
     !disabled_retire_stop_resources_empty(&rebind.start.stop)||
     rebind.start.start.admission.snapshot.active||rebind.start.start.admission.snapshot.token||
     rebind.stop.owner!=getpid()||rebind.stop.busy||!rebind.stop.complete||
     rebind.stop.active!=&rebind.start||!disabled_retire_stop_empty(&rebind.stop.stop))return 0;
  stop=&rebind.stop.stop;attempt=&rebind.start.open.attempt;
  id=rebind.stop.id;created=rebind.stop.created;
 }else{
  if(backend.phase!=WR_IOT_OWNER_OFF)return 0;
  stop=&backend.stop.stop;attempt=&backend.start.open.attempt;
  id=backend.stop.id;created=backend.stop.created;
 }
 /* Old CLOSE is retained identity, not a fresh lease in the new Main epoch.
  * The independent new idle observation below proves the replacement state. */
 return memchr(id,0,33)&&wr_iot_control_id(id)&&created&&
  strcmp(next->id,id)&&next->created>=created&&
  p->epoch==attempt->identity.adapter_epoch&&p->generation==attempt->identity.device_generation&&
  p->open_token==stop->close.request.open_token&&p->closed_serial==stop->close_serial;
}
static int disabled_retire_same_idle(const struct wr_iot_initial_off *a,
 const struct wr_iot_initial_off *b)
{
 return a->owner==getpid()&&a->ready==1&&a->created==b->created&&
  memchr(a->id,0,sizeof(a->id))&&!strcmp(a->id,b->id)&&!memcmp(a->nonce,b->nonce,16)&&
  a->idle.epoch==b->idle.epoch&&a->idle.generation==b->idle.generation&&a->idle.serial==b->idle.serial;
}
int wr_iot_rc_on_disabled_backend_retire(struct wr_iot_on_disabled *s,
 const struct wr_iot_physical_stop_request *previous)
{
 struct wr_iot_on_restore *r;struct wr_iot_initial_off next;unsigned char before[64],after[64];int guard,ok=0;
 if(!s||!previous||s->owner!=getpid()||s->busy||!s->restore||
    initial_restart_retained()||wr_iot_cold_backend_parent||
    previous->action!=WR_STOP_RELEASE||!wr_iot_physical_stop_request_valid(previous)||
    !disabled_retire_route_ready()||
    !wr_iot_rc_shutdown.radio_on_owned||wr_iot_rc_shutdown.radio_off_owned||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending)return 0;
 r=s->restore;next=s->idle;
 if(r->owner!=getpid()||r->busy||r->phase!=WR_ON_RESTORE_DONE||r->handoff_created||
    r->generation.phase!=WR_ON_GEN_COMMITTED||r->generation.admission||
    next.owner!=getpid()||next.ready!=1||!next.created||!next.idle.serial||
    !memchr(next.id,0,sizeof(next.id))||!wr_iot_control_id(next.id)||
    memcmp(next.nonce,r->open_id,16)||
    next.idle.epoch!=r->main.identity.adapter_epoch||
    next.idle.generation!=r->main.identity.device_generation||
    next.idle.epoch<=previous->epoch||next.idle.generation!=previous->generation||
    !wr_iot_physical_stop_request_encode(before,sizeof(before),previous)||
    !wr_iot_physical_stop_request_encode(after,sizeof(after),&r->profile_origin)||
    memcmp(before,after,sizeof(before)))return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 /* Same completed transfer can be retried before its caller drops exclusion. */
 if(!rebind.owner&&backend.owner==getpid()&&!backend.busy&&
    backend.phase==WR_IOT_OWNER_INITIAL_OFF&&!backend.start.owner&&!backend.stop.owner&&
    disabled_retire_same_idle(&backend.initial_off,&next)){
  struct wr_iot_profile_binding binding={0};struct wr_iot_restart_profile_receipt profile={0};
  ok=wr_iot_rc_profile_history_read(&binding,&profile)&&
   wr_iot_restart_profile_receipt_current(&r->profile_receipt)&&
   !strcmp(r->profile_receipt.path,profile.path)&&wr_iot_on_disabled_followup(s);
  goto done;
 }
 if(!disabled_retire_old_release(previous,&next)||!wr_iot_on_disabled_followup(s)||
    !wr_iot_restart_profile_receipt_current(&r->profile_receipt)||
    !wr_iot_initial_off_observed(&next)||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||
    !disabled_retire_route_ready())goto done;
 /* All fallible observations precede the transfer. Signal handlers only mark
  * route/admission fields; no callback can observe these private half-writes.
  * Old contexts have no live resource. Wipe possible historical credentials. */
 {volatile unsigned char *p=(volatile unsigned char *)&backend;size_t n=sizeof(backend);while(n--)*p++=0;}
 {volatile unsigned char *p=(volatile unsigned char *)&rebind;size_t n=sizeof(rebind);while(n--)*p++=0;}
 {struct wr_iot_profile_binding binding={.kind=WR_PROFILE_BACKEND_INITIAL_OFF};
  memcpy(binding.id,next.id,sizeof(binding.id));binding.created=next.created;
  binding.identity.adapter_epoch=next.idle.epoch;binding.identity.device_generation=next.idle.generation;
  profile_history_commit(&binding,&r->profile_receipt);
 }
 backend.initial_off=next;backend.owner=getpid();backend.phase=WR_IOT_OWNER_INITIAL_OFF;ok=1;
 done:wr_iot_service_guard_leave(guard);return ok;
}
