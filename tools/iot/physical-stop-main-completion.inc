/* Software checked-close completion, never a new RF/firmware certificate.
 * Caller owns RTNL and adapter lifetime. No waits, puts, hardware or queue work.
 * Main release predicate includes callback join and actual native dev_put return.
 */
static INT __attribute__((unused)) wr_iot_physical_stop_main_complete(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,unsigned long serial)
{
 struct wr_iot_physical_stop_request request;
 struct wr_iot_interface_ref *main_record;
 struct wr_iot_physical_stop_lifetime *s;
 unsigned long completion_epoch;unsigned long long prior;ULONG flags=0;
 unsigned int shutdown_stage,off_stage,down_stage;int exact,finished=0;
 if(!ad||!main_dev||!serial)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 s=&ad->wr_iot_physical_lifetime;
 main_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   main_dev,s->main_generation);
 exact=s->main_device==main_dev&&
  wr_iot_physical_stop_lifetime_main_released(s,serial,&ad->wr_iot_main_recovery,
    &ad->wr_iot_transition,main_record,VIRTUAL_IF_NUM(ad));
 request=s->arm_request;prior=s->arm_record_serial;
 completion_epoch=ad->wr_iot_transition.epoch;
 shutdown_stage=ad->wr_iot_transition.shutdown_stage;
 off_stage=ad->wr_iot_transition.mt_radio_off_stage;
 down_stage=ad->wr_iot_transition.virtual_down_stage;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact||shutdown_stage!=2U||off_stage!=4U||down_stage!=2U)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 if(request.action==WR_STOP_ARM&&prior!=~0ULL&&
    ad->wr_iot_physical_stop.serial==prior+1&&
    ad->wr_iot_physical_pins.module==1&&ad->wr_iot_physical_pins.task&&
    ad->wr_iot_physical_pins.device==(struct net_device *)main_dev&&
    ad->wr_iot_physical_stop.open_token==request.open_token&&
    ad->wr_iot_physical_stop.closed_serial==request.closed_serial){
  if(ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_COMPLETE)
   finished=ad->wr_iot_physical_stop.completion_epoch==completion_epoch&&
    wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor)&&
    ad->wr_iot_peer_table_owner.closed&&!ad->wr_iot_peer_table_owner.active&&
    !ad->wr_iot_peer_table_owner.retained&&!ad->wr_iot_peer_table_owner.poisoned&&
    !ad->wr_iot_peer_table_owner.transactions&&
    wr_iot_physical_stop_observe(&ad->wr_iot_physical_stop,prior+1,request.epoch,
      request.generation,request.open_token,request.closed_serial,request.nonce,
      ad->wr_iot_physical_pins.task);
  else finished=wr_iot_physical_stop_finish_checked_at_epoch(
    &ad->wr_iot_physical_stop,prior+1,request.epoch,request.generation,
    request.nonce,ad->wr_iot_physical_pins.task,&ad->wr_iot_peer_close_executor,
    &ad->wr_iot_peer_table_owner,exact,shutdown_stage,off_stage,down_stage,completion_epoch);
 }
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 return finished?0:-EUCLEAN;
}
