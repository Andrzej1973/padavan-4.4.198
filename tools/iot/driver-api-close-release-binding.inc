/* Experimental no-host beacon build only. Include after the existing CLOSE
 * progress and CLOSED probe implementations. Common ioctl must hold RTNL and
 * authorize CAP_NET_ADMIN before decoding a request for this binding.
 * RF/DMA packet release remains with the existing SDK owners. */
#ifndef WR_IOT_RA2_NO_HOST_MODE
#error "CLOSE release requires the complete immutable ra2 no-host mode"
#endif
#include "driver-api-close-release.h"
static INT wr_iot_driver_close_release(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_driver_close_request *request)
{
 ULONG flags=0;
 unsigned long producer_generation;
 struct wr_iot_beacon_producer_gate producer;
 int exact,status,released;
 if(!ad||!dev||!request)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 exact=IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&ad->net_dev!=dev&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&
  !ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned;
 released=!ad->wr_iot_close_owner.active;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EBUSY;
 if(!released){
  status=wr_iot_driver_close_progress(ad,dev,request);
  if(status)return status;
 }
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 producer_generation=ad->wr_iot_beacon_gates[2].generation;
 exact=producer_generation&&
  wr_iot_beacon_gate_drained(&ad->wr_iot_beacon_gates[2],producer_generation);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 if(!exact)return -EAGAIN;
 if(!released){
  status=wr_iot_mt7603_closed_probe(ad,dev,&ad->wr_iot_closed_probe,
   ad->wr_iot_close_owner.generation,ad->wr_iot_close_owner.open_token,
   ad->wr_iot_close_owner.ticket.serial);
  if(status)return status;
 }
 /* Keep the locks disjoint. RTNL excludes generation-changing virtual
  * open/close. A concurrent reset must publish transition intent, which the
  * locked reference predicate rejects before committing this snapshot. */
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 producer=ad->wr_iot_beacon_gates[2];
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 exact=!ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  wr_iot_driver_close_release_reference(&ad->wr_iot_close_owner,
   &ad->wr_iot_driver_owner,request,&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,dev,VIRTUAL_IF_NUM(ad),
   &ad->wr_iot_closed_probe,&producer,producer_generation);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return exact?0:-EAGAIN;
}
