/* Caller owns RTNL/outer adapter lifetime and persistent terminal storage.
 * No physical teardown or waits. Once Main close begins, CANCEL must refuse.
 * Terminal is prepared before mutation, committed only after actual puts/end.
 * Include after admission, pins and terminal helpers. */
static INT __attribute__((unused)) wr_iot_physical_stop_cancel_owned(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_stop_request *request,unsigned long serial,
 struct wr_iot_physical_stop_terminal *terminal)
{
 struct wr_iot_physical_stop_lifetime *s;
 struct wr_iot_interface_ref *main_record;
 ULONG flags=0;int exact,detached,idle,returned,ended;
 if(!ad||!main_dev||!serial||!terminal||
    !wr_iot_physical_stop_request_valid(request)||request->action!=WR_STOP_CANCEL)
  return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!wr_iot_physical_stop_terminal_prepare(terminal,request))return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 s=&ad->wr_iot_physical_lifetime;
 main_record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev);
 exact=s->active&&s->serial==serial&&s->main_device==main_dev&&!s->main_ticket_valid&&
  s->arm_request.action==WR_STOP_ARM&&request->epoch==s->arm_request.epoch&&
  request->generation==s->arm_request.generation&&request->open_token==s->arm_request.open_token&&
  request->closed_serial==s->arm_request.closed_serial&&
  wr_iot_physical_stop_nonce_equal(request->nonce,s->arm_request.nonce)&&
  s->arm_record_serial!=~0ULL&&request->attempt==s->arm_record_serial+1&&
  main_record&&main_record->generation==s->main_generation&&
  main_record->last_token==s->main_open_token&&main_record->published&&!main_record->removing&&
  main_record->family==WR_REF_FAMILY_MAIN&&
  ad->wr_iot_main_recovery.phase==WR_MAIN_OWNER_IDLE&&!ad->wr_iot_main_recovery.deferred_owners&&
  ad->wr_iot_transition.serial==s->arm_radio_serial&&
  ad->wr_iot_transition.epoch==s->arm_radio_epoch&&
  ad->wr_iot_transition.phase==WR_RADIO_READY&&!ad->wr_iot_transition.busy&&
  ad->wr_iot_transition.main_ready&&!ad->wr_iot_transition.main_inhibited&&
  !ad->wr_iot_transition.retiring&&!ad->wr_iot_transition.reset_pending&&
  !ad->wr_iot_transition.pm_suspending&&!ad->wr_iot_transition.pm_suspended;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact){wr_iot_physical_stop_terminal_clear(terminal);return -EBUSY;}
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 detached=wr_iot_physical_stop_pins_detach(&ad->wr_iot_physical_pins,
  &ad->wr_iot_physical_pending_pins,&ad->wr_iot_physical_stop,request->attempt,
  request->epoch,request->generation,request->nonce,1);
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!detached){wr_iot_physical_stop_terminal_clear(terminal);return -EBUSY;}
 returned=wr_iot_physical_stop_pins_drop(&ad->wr_iot_physical_pending_pins);
 if(!returned)return -EUCLEAN; /* persistent references/cache remain owned */
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 idle=!wr_iot_physical_stop_blocks_retirement(&ad->wr_iot_physical_stop,
    &ad->wr_iot_physical_pins)&&!ad->wr_iot_physical_pending_pins.module&&
    !ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ended=wr_iot_physical_stop_lifetime_end(&ad->wr_iot_physical_lifetime,serial,idle,returned);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_physical_stop_terminal_commit(terminal,idle,returned,ended))return -EUCLEAN;
 return 0;
}
