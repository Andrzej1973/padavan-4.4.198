/* Uncomposed RC-private disabled followup: never substitutes ACTIVE proof. */
static int wr_iot_cold_disabled_followup_current(const struct wr_iot_cold_disabled_release *r)
{
 int guard,ok;
 if(!r||r->owner!=getpid()||r->busy||r->parent||r->disabled||!r->created||
    !memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id)||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned||
    !wr_iot_rc_shutdown.radio_on_owned||!wr_iot_cold_disabled_backend_idle()||
    backend.owner!=getpid()||backend.phase!=WR_IOT_OWNER_INITIAL_OFF||
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
  wr_iot_cold_policy_current(&r->policy)&&wr_iot_restart_profile_receipt_current(&r->profile)&&
  !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending;
 wr_iot_service_guard_leave(guard);return ok;
}
static int wr_iot_cold_disabled_followup_wan(struct wr_iot_cold_disabled_release *r)
{
 return wr_iot_cold_disabled_followup_current(r)&&r->wan.owner==getpid()&&r->wan.radio_on==1&&
  wr_iot_wan_followup_step(&r->wan)&&wr_iot_cold_disabled_followup_current(r);
}
