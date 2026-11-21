/* Dormant never-opened ARM admission. Existing RTNL and adapter/Main pins
 * belong to caller. No hardware work, native ref acquisition or fake CLOSE. */
static INT __attribute__((unused)) wr_iot_physical_initial_arm_admit(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_initial_request *request,unsigned long *serial)
{
 struct wr_iot_interface_ref *main_record;PNET_DEV iot_dev;
 ULONG flags=0;int exact;unsigned long accepted=0;
 if(serial)*serial=0;
 if(!ad||!main_dev||!serial||!wr_iot_physical_initial_valid(request,0)||
    request->action!=WR_STOP_ARM)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 exact=!ad->wr_iot_physical_initial.task&&!ad->wr_iot_physical_initial.status&&
  ad->wr_iot_physical_initial.serial!=~0ULL&&
  ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&!ad->wr_iot_physical_stop.task&&
  !ad->wr_iot_physical_pins.module&&!ad->wr_iot_physical_pins.task&&
  !ad->wr_iot_physical_pins.device&&!ad->wr_iot_physical_pending_pins.module&&
  !ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device&&
  !ad->wr_iot_physical_terminal.owner&&!ad->wr_iot_physical_initial_terminal.owner&&
  wr_iot_peer_close_executor_idle(&ad->wr_iot_peer_close_executor)&&
  wr_iot_peer_table_allows(&ad->wr_iot_peer_table_owner,0)&&
  !ad->wr_iot_peer_table_owner.transactions;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!exact)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 iot_dev=ad->ApCfg.MBSSID[2].wdev.if_dev;
 exact=ad->net_dev==main_dev&&ad->ApCfg.BssidNum==3&&iot_dev&&iot_dev!=main_dev&&
  !ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active&&
  request->epoch==ad->wr_iot_idle_probe.ticket.epoch&&
  request->idle_serial==ad->wr_iot_idle_probe.ticket.serial&&
  request->generation==ad->wr_iot_idle_probe.generation&&
  wr_iot_precreated_idle_probe_current(&ad->wr_iot_idle_probe,
    &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
    main_dev,iot_dev,request->generation,VIRTUAL_IF_NUM(ad));
 main_record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev);
 if(exact)accepted=wr_iot_physical_stop_lifetime_begin_main(
  &ad->wr_iot_physical_lifetime,&ad->wr_iot_transition,
  &ad->wr_iot_main_recovery,main_record,main_dev);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!accepted)return -EAGAIN;
 *serial=accepted;return 0;
}
