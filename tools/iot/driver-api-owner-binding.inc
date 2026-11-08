/* Adapter bindings for the new synchronous OPEN entry. Not installed yet.
 * The ioctl RTNL/lifetime contract must already hold. No sleeping, PBKDF,
 * netdev open or user-memory access occurs under the transition spinlock. */
static INT wr_iot_driver_request_enter(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_open_request *request,const void *task)
{
 ULONG flags=0;int accepted=0;
 if(!ad||!dev||!request||!task||task!=current)return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(IS_MT7603(ad)&&ad->ApCfg.BssidNum>=3&&
    ad->ApCfg.BssidNum<=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0])&&
    ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&ad->net_dev!=dev){
  accepted=wr_iot_driver_owner_reserve(&ad->wr_iot_driver_owner,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,dev,VIRTUAL_IF_NUM(ad),task,request,ad->wr_iot_control_users,
   ad->wr_iot_control_poisoned||ad->wr_iot_boot_active||ad->wr_iot_boot_failed);
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return accepted?0:-EBUSY;
}
static INT wr_iot_driver_request_leave(RTMP_ADAPTER *ad,PNET_DEV dev,const void *task)
{
 ULONG flags=0;int clean,wake;unsigned long prior_retired;
 if(!ad||!dev||!task||task!=current)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 prior_retired=ad->wr_iot_transition.retired_serial;
 clean=wr_iot_driver_owner_leave(&ad->wr_iot_driver_owner,task,dev,
  &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1);
 if(ad->wr_iot_driver_owner.poisoned)ad->wr_iot_control_poisoned=1;
 wake=prior_retired!=ad->wr_iot_transition.retired_serial;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(wake)wake_up_all(&ad->wr_iot_ticket_wait);
 return clean;
}
