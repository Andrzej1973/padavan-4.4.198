/* Internal initial-registration configuration observation only. Caller owns
 * RTNL and adapter/netdev lifetime plus persistent probe storage. No endpoint
 * installed here. EUCLEAN retains active context and poisons admission. */
static INT wr_iot_precreated_idle_probe_driver(PRTMP_ADAPTER ad,PNET_DEV dev,
 struct wr_iot_precreated_idle_probe *probe,unsigned long generation)
{
 ULONG flags=0;int begun=0,observed,accepted,status,wake=0,eligible;
 if(!ad||!dev||!probe)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 eligible=IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&dev!=ad->net_dev&&
  !ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active;
 if(eligible)begun=wr_iot_precreated_idle_probe_begin(probe,
  &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  ad->net_dev,dev,generation,VIRTUAL_IF_NUM(ad));
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!begun)return -EBUSY;
 observed=wr_iot_mt7603_closed_config_observed(ad,dev);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 eligible=IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&dev!=ad->net_dev&&
  !ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active;
 accepted=wr_iot_precreated_idle_probe_finish(probe,&ad->wr_iot_transition,
  ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad),
  eligible?observed:0);
 if(probe->active){ad->wr_iot_control_poisoned=1;status=-EUCLEAN;}
 else{wake=1;status=accepted?0:-EAGAIN;}
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(wake)wake_up_all(&ad->wr_iot_ticket_wait);
 return status;
}
