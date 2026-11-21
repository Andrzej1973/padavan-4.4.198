/* Uncomposed RC-private followup observer after parent release. No borrowed
 * cold-parent pointer or credential reconstruction. Existing backend retains
 * its independent ACTIVE owner, request and normal stop resources. */
static int wr_iot_cold_followup_active(const struct wr_iot_cold_release *r)
{
 struct wr_iot_control_result observed={0};int guard,ok;
 if(!r||r->owner!=getpid()||r->busy||r->parent||r->handoff||
    !r->created||!memchr(r->id,0,sizeof(r->id))||!wr_iot_control_id(r->id)||
    !r->identity.adapter_epoch||!r->identity.device_generation||
    wr_iot_cold_backend_parent||rebind.owner||backend.owner!=getpid()||backend.busy||
    backend.phase!=WR_IOT_OWNER_ACTIVE||backend.start.owner!=getpid()||backend.start.busy||
    backend.start.phase!=WR_IOT_RUN_ACTIVE||
    !memchr(backend.start.input.id,0,sizeof(backend.start.input.id))||
    strcmp(r->id,backend.start.input.id)||r->created!=backend.start.input.created||
    r->identity.adapter_epoch!=backend.start.open.attempt.identity.adapter_epoch||
    r->identity.device_generation!=backend.start.open.attempt.identity.device_generation||
    wr_iot_rc_shutdown.active||wr_iot_rc_shutdown.pending||wr_iot_rc_shutdown.radio_off_owned||
    !wr_iot_rc_shutdown.radio_on_owned)return 0;
 guard=wr_iot_service_guard_enter(1);if(guard!=1)return 0;
 memcpy(observed.id,r->id,sizeof(observed.id));observed.created=r->created;observed.state=WR_IOT_RESULT_APPLIED;
 ok=wr_iot_cold_policy_current(&r->policy)&&wr_iot_restart_profile_receipt_current(&r->profile)&&
  wr_iot_activation_owner_observed(&backend,&observed)&&
  wr_iot_restart_profile_receipt_current(&r->profile)&&
  !wr_iot_rc_shutdown.active&&!wr_iot_rc_shutdown.pending&&wr_iot_cold_policy_current(&r->policy);
 wr_iot_service_guard_leave(guard);return ok;
}
/* One existing WAN followup attempt. A successful return is SDK return plus
 * fresh ACTIVE/profile proof, not WAN connectivity or final root completion. */
static int wr_iot_cold_followup_wan(struct wr_iot_cold_release *r)
{
 if(!wr_iot_cold_followup_active(r)||r->wan.owner!=getpid()||r->wan.radio_on!=1)return 0;
 return wr_iot_wan_followup_step(&r->wan)&&wr_iot_cold_followup_active(r);
}
