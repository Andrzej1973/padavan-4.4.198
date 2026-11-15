/* Private RC fragment after cold backend declarations. No baseline rollback:
 * completed normal OFF owns its current profile mutation independently. */
int wr_iot_rc_cold_shutdown_closed(const struct wr_iot_cold_owner *p,
 const struct wr_iot_cold_handoff *handoff,const struct wr_iot_rc_quiesce *off,
 struct wr_iot_driver_closed_result *out)
{
 struct wr_iot_control_result result={0};struct wr_iot_driver_closed_result closed={0};
 int guard,ok=0;size_t i;
 if(!out)return 0;
 memset(out,0,sizeof(*out));
 if(!p||!handoff||!off||wr_iot_cold_backend_parent!=p||p->owner!=getpid()||p->busy||
    handoff->owner!=getpid()||handoff->busy||handoff->parent!=p||!handoff->attempted||!handoff->backend_claimed||
    (handoff->phase!=WR_COLD_HANDOFF_WAIT&&handoff->phase!=WR_COLD_HANDOFF_ACTIVE)||
    !handoff->created||!memchr(handoff->id,0,sizeof(handoff->id))||!wr_iot_control_id(handoff->id)||
    rebind.owner||backend.owner!=getpid()||backend.busy||backend.phase!=WR_IOT_OWNER_OFF||
    backend.start.owner!=getpid()||backend.start.busy||backend.start.phase!=WR_IOT_RUN_STOPPED||
    !memchr(backend.start.input.id,0,sizeof(backend.start.input.id))||
    strcmp(handoff->id,backend.start.input.id)||handoff->created!=backend.start.input.created||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||off->owner!=getpid()||off->busy||off->active||!off->complete||off->resume_needed||
    !off->created||!memchr(off->id,0,sizeof(off->id))||!wr_iot_control_id(off->id)||
    !strcmp(off->id,handoff->id)||off->created<handoff->created||
    backend.stop.owner!=getpid()||backend.stop.busy||backend.stop.active!=&backend.start||
    !backend.stop.complete||!memchr(backend.stop.id,0,sizeof(backend.stop.id))||
    strcmp(off->id,backend.stop.id)||off->created!=backend.stop.created||
    p->main.identity.adapter_epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    p->main.identity.device_generation!=wr_iot_cold_backend_identity.device_generation||
    handoff->identity.adapter_epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    handoff->identity.device_generation!=wr_iot_cold_backend_identity.device_generation)return 0;
 for(i=0;i<sizeof(off->desired);i++)if(((const unsigned char*)&off->desired)[i])return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 memcpy(result.id,off->id,sizeof(result.id));result.created=off->created;result.state=WR_IOT_RESULT_APPLIED;
 if(wr_iot_activation_owner_closed(&backend,&result,&closed)&&closed.open_token&&closed.close_serial&&
    closed.adapter_epoch==wr_iot_cold_backend_identity.adapter_epoch&&
    closed.device_generation==wr_iot_cold_backend_identity.device_generation&&
    closed.open_token==backend.stop.stop.close.request.open_token&&
    closed.close_serial==backend.stop.stop.close_serial&&
    closed.adapter_epoch==backend.start.open.attempt.identity.adapter_epoch&&
    closed.device_generation==backend.start.open.attempt.identity.device_generation){*out=closed;ok=1;}
 wr_iot_service_guard_leave(guard);return ok;
}

int wr_iot_rc_cold_shutdown_rejected(const struct wr_iot_cold_owner *p,
 const struct wr_iot_cold_handoff *h)
{
 struct wr_iot_idle_result before={0},after={0};unsigned i;int guard,ok;
 if(!p||!h||wr_iot_cold_backend_parent!=p||p->owner!=getpid()||p->busy||
    h->owner!=getpid()||h->busy||h->parent!=p||!h->attempted||!h->backend_claimed||
    (h->phase!=WR_COLD_HANDOFF_WAIT&&h->phase!=WR_COLD_HANDOFF_ACTIVE)||
    !h->created||!memchr(h->id,0,sizeof(h->id))||!wr_iot_control_id(h->id)||
    rebind.owner||backend.owner!=getpid()||backend.busy||backend.phase!=WR_IOT_OWNER_REJECTED||
    backend.start.owner!=getpid()||backend.start.busy||backend.start.phase!=WR_IOT_RUN_REJECTED||
    !memchr(backend.start.input.id,0,sizeof(backend.start.input.id))||
    strcmp(h->id,backend.start.input.id)||h->created!=backend.start.input.created||
    backend.start.admission.snapshot.active||backend.start.admission.snapshot.token||
    (backend.start.admission.mutation_started&&backend.start.rollback.phase!=WR_IOT_ROLL_DONE)||
    backend.start.close.owner||backend.stop.owner||
    (backend.start.open.phase!=WR_IOT_OPEN_IDLE&&backend.start.open.phase!=WR_IOT_OPEN_NOT_SUBMITTED)||
    (backend.start.open.phase==WR_IOT_OPEN_IDLE&&backend.start.open.owner)||
    (backend.start.open.owner&&backend.start.open.owner!=getpid())||
    backend.start.open.attempt.identity.adapter_epoch||backend.start.open.attempt.identity.device_generation||
    !wr_iot_rc_shutdown.active||!wr_iot_rc_shutdown.radio_off_owned||wr_iot_rc_shutdown.radio_on_owned||
    (wr_iot_rc_shutdown.pending!=SIGTERM
#ifdef SIGQUIT
     &&wr_iot_rc_shutdown.pending!=SIGQUIT
#endif
    )||h->identity.adapter_epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    h->identity.device_generation!=wr_iot_cold_backend_identity.device_generation||
    p->main.identity.adapter_epoch!=wr_iot_cold_backend_identity.adapter_epoch||
    p->main.identity.device_generation!=wr_iot_cold_backend_identity.device_generation)return 0;
 for(i=0;i<16;i++)if(backend.start.open.attempt.request_id[i])return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 ok=!if_nametoindex("br-iot")&&wr_iot_request_initial_off_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0&&
  wr_iot_driver_initial_idle_read(p->admission.nonce,&before)&&
  wr_iot_driver_initial_idle_read(p->admission.nonce,&after)&&
  before.epoch==wr_iot_cold_backend_identity.adapter_epoch&&before.generation==wr_iot_cold_backend_identity.device_generation&&
  before.serial&&after.serial>before.serial&&after.epoch==before.epoch&&after.generation==before.generation&&
  !if_nametoindex("br-iot")&&wr_iot_request_initial_off_current()&&wr_iot_bss_is_down()&&
  wr_iot_dns_activation_recovery_state()==0;
 wr_iot_service_guard_leave(guard);return ok;
}
