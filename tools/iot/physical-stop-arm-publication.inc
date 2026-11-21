/* Caller-owned local bundle survives every refusal. This operation transfers
 * it into the retained slot only on success; no allocations, drops or waits.
 * Caller owns RTNL, outer adapter lifetime and persistent storage for slot/local.
 * Include after ARM admission and physical-stop-pins.inc. */
static INT __attribute__((unused)) wr_iot_physical_stop_arm_publish_owned(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_stop_request *request,unsigned long serial,
 struct wr_iot_physical_stop_pins *slot,
 struct wr_iot_physical_stop_pins *local,unsigned long long *attempt)
{
 struct wr_iot_physical_stop_lifetime *s;
 struct wr_iot_interface_ref *record;
 unsigned long long record_serial;ULONG flags=0;int exact,published=0;
 if(!ad||!main_dev||!slot||!local||slot==local||!attempt||!serial||
    !wr_iot_physical_stop_request_valid(request)||request->action!=WR_STOP_ARM)
  return -EINVAL;
 if(slot!=&ad->wr_iot_physical_pins||local!=&ad->wr_iot_physical_pending_pins)
  return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 s=&ad->wr_iot_physical_lifetime;
 record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev);
 exact=s->active&&s->serial==serial&&s->main_device==main_dev&&
  s->arm_request.action==WR_STOP_ARM&&
  request->epoch==s->arm_request.epoch&&
  request->generation==s->arm_request.generation&&
  request->open_token==s->arm_request.open_token&&
  request->closed_serial==s->arm_request.closed_serial&&
  wr_iot_physical_stop_nonce_equal(request->nonce,s->arm_request.nonce)&&
  !s->main_ticket_valid&&record&&record->generation==s->main_generation&&
  record->last_token==s->main_open_token&&record->published&&!record->removing&&
  record->family==WR_REF_FAMILY_MAIN&&
  ad->wr_iot_main_recovery.phase==WR_MAIN_OWNER_IDLE&&
  !ad->wr_iot_main_recovery.deferred_owners&&
  ad->wr_iot_transition.serial==s->arm_radio_serial&&
  ad->wr_iot_transition.epoch==s->arm_radio_epoch&&
  request->epoch==s->arm_radio_epoch&&
  ad->wr_iot_transition.phase==WR_RADIO_READY&&!ad->wr_iot_transition.busy&&
  !ad->wr_iot_transition.retiring&&!ad->wr_iot_transition.reset_pending;
 record_serial=s->arm_record_serial;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EBUSY;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 if(local->device==(struct net_device *)main_dev&&
    ad->wr_iot_physical_stop.serial==record_serial)
  published=wr_iot_physical_stop_pins_publish(slot,local,&ad->wr_iot_physical_stop,
   request->epoch,request->generation,request->open_token,request->closed_serial,
   request->nonce,&ad->wr_iot_peer_close_executor);
 if(published)*attempt=ad->wr_iot_physical_stop.serial;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 return published?0:-EBUSY;
}
