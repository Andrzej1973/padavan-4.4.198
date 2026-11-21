/* INITIAL_OFF publication only. Caller owns RTNL, adapter and Main lifetime;
 * local references were obtained by the existing native pins_acquire outside
 * locks. Refusal leaves the bundle owned by the caller; no puts occur here. */
static INT __attribute__((unused)) wr_iot_physical_initial_arm_publish(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_initial_request *request,
 struct wr_iot_physical_stop_pins *local,unsigned long long *attempt)
{
 struct wr_iot_physical_initial_origin origin={0};
 struct wr_iot_physical_stop_lifetime life;
 struct wr_iot_interface_ref iot;
 struct wr_iot_interface_ref *record;
 ULONG flags=0;int exact,published=0;
 if(!ad||!main_dev||!local||!attempt||
    !wr_iot_physical_initial_valid(request,0)||request->action!=WR_STOP_ARM)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(local!=&ad->wr_iot_physical_pending_pins)return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  ad->ApCfg.MBSSID[2].wdev.if_dev,request->generation);
 exact=record&&ad->net_dev==main_dev&&ad->ApCfg.BssidNum==3&&IS_MT7603(ad)&&
  !ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active&&
  wr_iot_physical_initial_capture(&origin,&ad->wr_iot_idle_probe,
   &ad->wr_iot_physical_lifetime,&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev,
   ad->ApCfg.MBSSID[2].wdev.if_dev,request->generation,VIRTUAL_IF_NUM(ad));
 if(exact){life=ad->wr_iot_physical_lifetime;iot=*record;}
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EAGAIN;
 /* RTNL and the retained Main lifetime exclude publication/registration
  * changes across these disjoint locks. No live transition fields read here. */
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 if(!ad->wr_iot_physical_pins.module&&!ad->wr_iot_physical_pins.task&&
    !ad->wr_iot_physical_pins.device&&local->module==1&&local->task==current&&
    local->device==(struct net_device *)main_dev&&
    ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&!ad->wr_iot_physical_stop.task&&
    wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor)&&
    wr_iot_peer_table_allows(&ad->wr_iot_peer_table_owner,0)&&
    !ad->wr_iot_peer_table_owner.transactions&&
    wr_iot_physical_initial_record_arm(&ad->wr_iot_physical_initial,
     request,current,&origin,&life,&iot)){
  ad->wr_iot_physical_pins=*local;
  local->module=0;local->task=NULL;local->device=NULL;
  *attempt=ad->wr_iot_physical_initial.serial;published=1;
 }
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 return published?0:-EAGAIN;
}
