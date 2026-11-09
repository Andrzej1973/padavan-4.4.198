/* Adapter bindings for the new synchronous OPEN entry. Not installed yet.
 * The ioctl RTNL/lifetime contract must already hold. No sleeping, PBKDF,
 * netdev open or user-memory access occurs under the transition spinlock. */
static INT wr_iot_driver_request_enter(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_open_request *request,const void *task)
{
 ULONG flags=0;int accepted=0;
 if(!ad||!dev||!request||!task||task!=current)return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 /* Lifetime retirement never grants permission to reopen a closed BSS. */
 if(!ad->wr_iot_close_owner.active&&IS_MT7603(ad)&&ad->ApCfg.BssidNum>=3&&
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

/* Caller holds transition_lock and its existing RTNL lifetime lease. */
static inline INT wr_iot_driver_first_beacon_owner_locked(RTMP_ADAPTER *ad,PNET_DEV dev)
{
 return IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&ad->net_dev&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&netif_running(dev)&&
  netif_running(ad->net_dev)&&!ad->wr_iot_close_owner.active&&
  !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  wr_iot_driver_owner_open_current(&ad->wr_iot_driver_owner,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,dev,VIRTUAL_IF_NUM(ad),current);
}
/* Snapshot only after ndo_open; never hold transition_lock across ring locks
 * or a future bounded wait. Revalidate the same snapshot after waking. */
static inline INT wr_iot_driver_first_beacon_owner_snapshot(RTMP_ADAPTER *ad,
 PNET_DEV dev,struct wr_iot_virtual_open_claim *snapshot)
{
 ULONG flags=0;int owned;
 if(!ad||!dev||!snapshot||!rtnl_is_locked())return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 owned=wr_iot_driver_first_beacon_owner_locked(ad,dev);
 if(owned)*snapshot=ad->wr_iot_driver_owner.claim;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return owned;
}
/* Called only after terminal consumption of a matching host publication.
 * This metadata is not a firmware ACK and grants no RF/TxS retirement. */
static inline INT wr_iot_driver_first_beacon_confirm(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_virtual_open_claim *expected)
{
 ULONG flags=0;int confirmed=0;
 const struct wr_iot_virtual_open_claim *now;
 if(!ad||!dev||!expected||!rtnl_is_locked())return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 now=&ad->wr_iot_driver_owner.claim;
 if(wr_iot_driver_first_beacon_owner_locked(ad,dev)&&
    !ad->wr_iot_driver_owner.receipt.first_beacon_confirmed&&
    now->device==expected->device&&now->generation==expected->generation&&
    now->epoch==expected->epoch&&now->serial==expected->serial&&
    now->operation==expected->operation){
  ad->wr_iot_driver_owner.receipt.first_beacon_confirmed=1;confirmed=1;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return confirmed;
}
