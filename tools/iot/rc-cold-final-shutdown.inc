/* RC-private post-parent-release shutdown, after cold completion fragments. */
#include "cold-on-root.h"
static int cold_final_pending(void)
{
 return wr_iot_rc_shutdown.active&&wr_iot_rc_shutdown.radio_on_owned&&
  !wr_iot_rc_shutdown.radio_off_owned&&(wr_iot_rc_shutdown.pending==SIGTERM
#ifdef SIGQUIT
  ||wr_iot_rc_shutdown.pending==SIGQUIT
#endif
 );
}
static int cold_final_enabled_binding(const struct wr_iot_cold_release *r)
{
 return r->owner==getpid()&&!r->busy&&!r->parent&&!r->handoff&&r->created&&
  memchr(r->id,0,sizeof(r->id))&&wr_iot_control_id(r->id)&&
  r->identity.adapter_epoch&&r->identity.device_generation&&
  backend.start.owner==getpid()&&!backend.start.busy&&
  memchr(backend.start.input.id,0,sizeof(backend.start.input.id))&&
  !strcmp(r->id,backend.start.input.id)&&r->created==backend.start.input.created&&
  r->identity.adapter_epoch==backend.start.open.attempt.identity.adapter_epoch&&
  r->identity.device_generation==backend.start.open.attempt.identity.device_generation;
}
static int cold_final_closed(const struct wr_iot_cold_release *r,
 const struct wr_iot_rc_quiesce *off)
{
 struct wr_iot_control_result observed={0};struct wr_iot_driver_closed_result closed={0};
 int guard,ok=0;size_t i;
 if(!cold_final_enabled_binding(r)||backend.phase!=WR_IOT_OWNER_OFF||
    backend.start.phase!=WR_IOT_RUN_STOPPED||off->owner!=getpid()||off->busy||
    off->active||!off->complete||off->resume_needed||!off->created||
    !memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id)||
    !strcmp(off->id,r->id)||off->created<r->created||
    backend.stop.owner!=getpid()||backend.stop.busy||backend.stop.active!=&backend.start||
    !backend.stop.complete||!memchr(backend.stop.id,0,sizeof(backend.stop.id))||
    strcmp(off->id,backend.stop.id)||off->created!=backend.stop.created)return 0;
 for(i=0;i<sizeof(off->desired);i++)if(((const unsigned char *)&off->desired)[i])return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 memcpy(observed.id,off->id,sizeof(observed.id));observed.created=off->created;observed.state=WR_IOT_RESULT_APPLIED;
 ok=wr_iot_activation_owner_closed(&backend,&observed,&closed)&&
  closed.adapter_epoch==r->identity.adapter_epoch&&closed.device_generation==r->identity.device_generation&&
  closed.open_token&&closed.close_serial&&
  closed.open_token==backend.stop.stop.close.request.open_token&&
  closed.close_serial==backend.stop.stop.close_serial&&wr_iot_cold_policy_current(&r->policy);
 wr_iot_service_guard_leave(guard);return ok;
}
static int cold_final_initial_off(const struct wr_iot_cold_disabled_release *r)
{
 int guard,ok;
 if(r->owner!=getpid()||r->busy||r->parent||r->disabled||!r->created||
    !r->identity.adapter_epoch||!r->identity.device_generation||
    !memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id)||
    backend.phase!=WR_IOT_OWNER_INITIAL_OFF||backend.start.owner||backend.stop.owner||
    backend.start.admission.snapshot.active||backend.start.admission.snapshot.token||
    backend.initial_off.owner!=getpid()||!backend.initial_off.ready||
    !memchr(backend.initial_off.id,0,sizeof(backend.initial_off.id))||
    strcmp(r->id,backend.initial_off.id)||r->created!=backend.initial_off.created||
    r->identity.adapter_epoch!=backend.initial_off.idle.epoch||
    r->identity.device_generation!=backend.initial_off.idle.generation)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=
#if WR_IOT_SAVED_CONFIG_SNAPSHOT_PREPARED != 1
  wr_iot_restart_disabled_profile_current()&&
#endif
  wr_iot_restart_profile_receipt_current(&r->profile)&&
  wr_iot_cold_policy_current(&r->policy)&&wr_iot_initial_off_observed(&backend.initial_off)&&
  wr_iot_restart_profile_receipt_current(&r->profile)&&wr_iot_cold_policy_current(&r->policy);
 wr_iot_service_guard_leave(guard);return ok;
}
static void cold_final_cleanup(void *context)
{
 struct wr_iot_cold_root *s=context;volatile unsigned char *p=(volatile unsigned char *)s;size_t n=sizeof(*s);
 /* Independent RC backend remains completed OFF/INITIAL_OFF. No live root
  * allocations remain; terminal finish has released its guard already. */
 while(n--)*p++=0;
 wr_iot_rc_shutdown.radio_on_owned=0;
}
int wr_iot_rc_cold_root_final_shutdown(struct wr_iot_cold_root *s,
 const struct wr_iot_control_request *input)
{
 struct wr_iot_terminal_iapp *terminal;struct wr_iot_driver_closed_result closed={0};
 struct wr_iot_cold_release *r;int guard,valid;
 if(!s||s->owner!=getpid()||s->busy||s->phase!=WR_COLD_ROOT_TERMINAL||
    (s->enabled!=0&&s->enabled!=1)||!cold_final_pending()||wr_iot_cold_backend_parent||
    rebind.owner||backend.owner!=getpid()||backend.busy||
    s->parent.owner||s->parent.generation.owner||s->parent.main.owner||s->parent.guest.owner||
    s->parent.services.owner||s->parent.multicast.owner||
    s->parent.admission.profile.files.count||s->parent.admission.guard||
    s->parent.admission.fence.owner||s->handoff.owner||s->stop.owner||s->stop.off.owner)return 0;
 if(s->enabled){
  if(s->disabled.owner||s->disabled_release.owner||s->disabled_terminal.owner||
     !s->released.released||s->released.busy||s->released.release!=&s->release||
     s->terminal.owner!=getpid()||s->terminal.busy||s->terminal.phase!=WR_COLD_TERM_IAPP||
     s->terminal.parent_release!=&s->released||!s->terminal.led_attempted||!s->terminal.led_returned||
     s->terminal.terminal.child!=&s->terminal.child||!cold_final_enabled_binding(&s->release))return 0;
  terminal=&s->terminal.terminal;
 }else{
  if(s->release.owner||s->terminal.owner||!s->disabled_released.released||s->disabled_released.busy||
     s->disabled_released.release!=&s->disabled_release||s->disabled_terminal.owner!=getpid()||
     s->disabled_terminal.busy||s->disabled_terminal.phase!=WR_COLD_DISABLED_TERM_IAPP||
     s->disabled_terminal.parent_release!=&s->disabled_released||
     !s->disabled_terminal.led_attempted||!s->disabled_terminal.led_returned||
     s->disabled_terminal.terminal.child!=&s->disabled_terminal.child||
     s->final_off_attempted||s->final_off.owner)return 0;
  terminal=&s->disabled_terminal.terminal;
 }
 s->busy=1;
 if(!wr_iot_terminal_iapp_shutdown_drain(terminal))goto retained;
 if(!s->enabled){if(!cold_final_initial_off(&s->disabled_release))goto retained;}
 else{
  r=&s->release;
  if(!s->final_off_attempted){
   if(!input||input->request.enabled||!input->created||input->created<r->created||
      !memchr(input->id,0,sizeof(input->id))||!wr_iot_control_id(input->id)||!strcmp(input->id,r->id)||
      input->request.ssid[0]||input->request.password[0]||input->request.gateway[0]||
      input->request.mask[0]||input->request.first[0]||input->request.last[0]||
      backend.phase!=WR_IOT_OWNER_ACTIVE||backend.start.phase!=WR_IOT_RUN_ACTIVE)goto retained;
   guard=wr_iot_service_guard_enter(1);if(guard!=1)goto retained;
   valid=wr_iot_restart_profile_receipt_current(&r->profile)&&wr_iot_cold_policy_current(&r->policy);
   wr_iot_service_guard_leave(guard);if(!valid)goto retained;
   s->final_off_attempted=1;
   /* Existing quiesce performs the full ACTIVE observation and erases its
    * resume intent. Refusal after this attempt must never replay OFF. */
   (void)wr_iot_rc_quiesce_shutdown_begin(&s->final_off,input);goto retained;
  }
  if(s->final_off.owner!=getpid()||
     !wr_iot_rc_quiesce_advance(&s->final_off,&closed)||
     !cold_final_closed(r,&s->final_off))goto retained;
 }
 if(wr_iot_terminal_iapp_shutdown_finish(terminal,cold_final_cleanup,s))return 1;
 retained:s->busy=0;return 0;
}
