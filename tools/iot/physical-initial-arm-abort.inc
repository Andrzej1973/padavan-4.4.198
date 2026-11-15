/* Unpublished ARM unwind only. Caller retains RTNL and independent adapter
 * lifetime, after returning every local native reference. Not a CANCEL API. */
static INT __attribute__((unused)) wr_iot_physical_initial_arm_abort_unpublished(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,unsigned long serial)
{
 struct wr_iot_physical_initial_origin origin={0};
 ULONG flags=0;int idle,ended=0;
 if(!ad||!main_dev||!serial)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 idle=!ad->wr_iot_physical_initial.task&&!ad->wr_iot_physical_initial.status&&
  ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&!ad->wr_iot_physical_stop.task&&
  !ad->wr_iot_physical_pins.module&&!ad->wr_iot_physical_pins.task&&
  !ad->wr_iot_physical_pins.device&&!ad->wr_iot_physical_pending_pins.module&&
  !ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device&&
  !ad->wr_iot_physical_terminal.owner&&!ad->wr_iot_physical_initial_terminal.owner;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!idle)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->net_dev==main_dev&&ad->ApCfg.BssidNum==3&&
    ad->wr_iot_physical_lifetime.serial==serial&&
    wr_iot_physical_initial_capture(&origin,&ad->wr_iot_idle_probe,
      &ad->wr_iot_physical_lifetime,&ad->wr_iot_transition,
      ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev,
      ad->ApCfg.MBSSID[2].wdev.if_dev,ad->wr_iot_idle_probe.generation,
      VIRTUAL_IF_NUM(ad))&&
    wr_iot_physical_initial_cancel_current(&origin,&ad->wr_iot_physical_lifetime,
      &ad->wr_iot_idle_probe,&ad->wr_iot_main_recovery,&ad->wr_iot_transition,
      ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad)))
  ended=wr_iot_physical_stop_lifetime_end(&ad->wr_iot_physical_lifetime,serial,1,1);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ended?0:-EAGAIN;
}
