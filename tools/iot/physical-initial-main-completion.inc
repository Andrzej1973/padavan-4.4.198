/* Candidate initial-origin completion binding. RTNL/lifetime owned by caller.
 * Only reads native completion receipts; no DOWN, hardware writes or puts.
 * MacTab and transition locks never nest. Initial record immutable under RTNL. */
static INT __attribute__((unused)) wr_iot_physical_initial_main_complete(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,unsigned long long attempt)
{
 struct wr_iot_physical_initial_record observed;
 struct wr_iot_interface_ref *main_record,*iot_record;
 struct wr_iot_physical_initial_request query;
 ULONG flags=0;unsigned long epoch;int exact,complete=0;
 if(!ad||!main_dev||!attempt)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 observed=ad->wr_iot_physical_initial;
 exact=observed.serial==attempt&&observed.task&&
  ad->wr_iot_physical_pins.module==1&&
  ad->wr_iot_physical_pins.task==observed.task&&
  ad->wr_iot_physical_pins.device==(struct net_device *)main_dev&&
  (observed.status==WR_STOP_RUNNING||observed.status==WR_STOP_COMPLETE);
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!exact)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 main_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  main_dev,observed.origin.main_generation);
 iot_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  ad->ApCfg.MBSSID[2].wdev.if_dev,observed.origin.generation);
 exact=observed.origin.main_device==main_dev&&
  wr_iot_physical_initial_main_released(&observed.origin,&ad->wr_iot_physical_lifetime,
   &ad->wr_iot_main_recovery,&ad->wr_iot_transition,main_record,iot_record,VIRTUAL_IF_NUM(ad))&&
  ad->wr_iot_transition.shutdown_stage==2U&&
  ad->wr_iot_transition.mt_radio_off_stage==4U&&
  ad->wr_iot_transition.virtual_down_stage==2U;
 epoch=ad->wr_iot_transition.epoch;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EAGAIN;
 query=observed.request;query.action=WR_STOP_QUERY;query.attempt=attempt;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 if(wr_iot_physical_initial_record_matches(&ad->wr_iot_physical_initial,&query,observed.task)&&
    ad->wr_iot_physical_pins.module==1&&ad->wr_iot_physical_pins.task==observed.task&&
    ad->wr_iot_physical_pins.device==(struct net_device *)main_dev&&
    wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor)&&
    ad->wr_iot_peer_table_owner.closed&&!ad->wr_iot_peer_table_owner.active&&
    !ad->wr_iot_peer_table_owner.retained&&!ad->wr_iot_peer_table_owner.poisoned&&
    !ad->wr_iot_peer_table_owner.transactions){
  if(ad->wr_iot_physical_initial.status==WR_STOP_RUNNING){
   ad->wr_iot_physical_initial.completion_epoch=epoch;
   ad->wr_iot_physical_initial.status=WR_STOP_COMPLETE;complete=1;
  }else if(ad->wr_iot_physical_initial.status==WR_STOP_COMPLETE)
   complete=ad->wr_iot_physical_initial.completion_epoch==epoch;
 }
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 return complete?0:-EAGAIN;
}
