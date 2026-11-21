/* Exact nonblocking state observation. No DOWN, work submission, puts or waits.
 * Handler may call main_complete separately before observing COMPLETE.
 * Caller owns RTNL and outer adapter/module lifetime; locks remain disjoint. */
static INT __attribute__((unused)) wr_iot_physical_stop_query_owned(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_stop_request *request,unsigned long serial,
 unsigned char *wire,unsigned int length)
{
 struct wr_iot_physical_stop_record observed;
 struct wr_iot_interface_ref *main_record,*iot_record;
 struct wr_iot_physical_stop_lifetime *s;
 struct wr_iot_radio_ticket captured;
 ULONG flags=0;unsigned status=0,i;int exact,phase_ok=0;
 if(!wire||length!=64)return -EINVAL;
 for(i=0;i<length;i++)wire[i]=0;
 if(!ad||!main_dev||!serial||!wr_iot_physical_stop_request_valid(request)||
    request->action!=WR_STOP_QUERY)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 observed=ad->wr_iot_physical_stop;
 exact=ad->wr_iot_physical_pins.module==1&&
  ad->wr_iot_physical_pins.task==current&&
  ad->wr_iot_physical_pins.device==(struct net_device *)main_dev&&
  observed.serial==request->attempt&&observed.open_token==request->open_token&&
  observed.closed_serial==request->closed_serial&&
  wr_iot_physical_stop_matches(&observed,request->attempt,request->epoch,
    request->generation,request->nonce,current);
 if(observed.phase==WR_PHYS_STOP_COMPLETE)
  exact=exact&&wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor)&&
   ad->wr_iot_peer_table_owner.closed&&!ad->wr_iot_peer_table_owner.active&&
   !ad->wr_iot_peer_table_owner.retained&&!ad->wr_iot_peer_table_owner.poisoned&&
   !ad->wr_iot_peer_table_owner.transactions;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!exact)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 s=&ad->wr_iot_physical_lifetime;
 main_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   main_dev,s->main_generation);
 iot_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->ApCfg.MBSSID[2].wdev.if_dev,request->generation);
 exact=s->active&&s->serial==serial&&s->main_device==main_dev&&
  s->arm_request.action==WR_STOP_ARM&&s->arm_record_serial!=~0ULL&&
  request->attempt==s->arm_record_serial+1&&request->epoch==s->arm_request.epoch&&
  request->generation==s->arm_request.generation&&request->open_token==s->arm_request.open_token&&
  request->closed_serial==s->arm_request.closed_serial&&
  wr_iot_physical_stop_nonce_equal(request->nonce,s->arm_request.nonce)&&
  iot_record&&iot_record->published&&!iot_record->removing&&
  iot_record->family==WR_REF_FAMILY_MBSS&&iot_record->phase==WR_REF_IDLE&&
  iot_record->last_token==request->open_token&&iot_record->close_serial==request->closed_serial&&
  !ad->wr_iot_transition.retiring&&!ad->wr_iot_transition.reset_pending&&
  !ad->wr_iot_transition.pm_suspending&&!ad->wr_iot_transition.pm_suspended;
 if(exact&&observed.phase==WR_PHYS_STOP_ARMED){
  phase_ok=main_record&&main_record->phase==WR_REF_OWNED&&
   main_record->last_token==s->main_open_token&&main_record->published&&!main_record->removing&&
   main_record->family==WR_REF_FAMILY_MAIN&&
   ad->wr_iot_transition.epoch==s->arm_radio_epoch&&
   ad->wr_iot_transition.serial==s->arm_radio_serial&&
   ad->wr_iot_transition.phase==WR_RADIO_READY&&!ad->wr_iot_transition.busy;
  status=WR_STOP_ARMED;
 }else if(exact&&observed.phase==WR_PHYS_STOP_RUNNING&&s->main_ticket_valid){
  phase_ok=wr_iot_main_recovery_capture_physical_ticket(&ad->wr_iot_main_recovery,
    &ad->wr_iot_transition,main_record,s->arm_radio_serial,
    s->main_generation,s->main_open_token,&captured)&&
   captured.serial==s->main_ticket.serial&&captured.epoch==s->main_ticket.epoch;
  if(!phase_ok)phase_ok=wr_iot_physical_stop_lifetime_main_released(s,serial,
    &ad->wr_iot_main_recovery,&ad->wr_iot_transition,main_record,VIRTUAL_IF_NUM(ad));
  status=WR_STOP_RUNNING;
 }else if(exact&&observed.phase==WR_PHYS_STOP_COMPLETE){
  phase_ok=observed.completion_epoch==ad->wr_iot_transition.epoch&&
   wr_iot_physical_stop_lifetime_main_released(s,serial,&ad->wr_iot_main_recovery,
    &ad->wr_iot_transition,main_record,VIRTUAL_IF_NUM(ad));
  status=WR_STOP_COMPLETE;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact||!phase_ok)return -EAGAIN;
 return wr_iot_physical_stop_response_encode(wire,length,request,observed.serial,status)?0:-EIO;
}
