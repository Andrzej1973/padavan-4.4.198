/* Dormant Linux ARM admission, not an endpoint or physical completion proof.
 * Caller holds RTNL and adapter/main-netdev/module lifetime. It must either
 * publish the physical record/pins or unwind this lifetime before returning.
 * Valid only with the verified immutable no-host ra2 beacon configuration. */
#ifndef WR_IOT_RA2_NO_HOST_MODE
#error "Physical ARM admission requires verified immutable ra2 no-host mode"
#endif
#include "physical-stop-prior-close.h"
#include "physical-stop-lifetime.h"
static INT __attribute__((unused)) wr_iot_physical_stop_arm_admit(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_stop_request *request,unsigned long *serial)
{
 struct wr_iot_beacon_producer_gate producer;
 struct wr_iot_interface_ref *main_record;
 PNET_DEV iot_dev;
 unsigned long producer_generation,accepted=0;ULONG flags=0;
 int exact;
 if(!ad||!main_dev||!serial||!wr_iot_physical_stop_request_valid(request)||
    request->action!=WR_STOP_ARM)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 producer=ad->wr_iot_beacon_gates[2];producer_generation=producer.generation;
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 iot_dev=ad->ApCfg.MBSSID[2].wdev.if_dev;
 exact=ad->net_dev==main_dev&&ad->ApCfg.BssidNum==3&&iot_dev&&iot_dev!=main_dev&&
  !ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
  !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  wr_iot_physical_stop_prior_close(request,&ad->wr_iot_close_owner,
   &ad->wr_iot_driver_owner,&ad->wr_iot_transition,ad->wr_iot_interface_refs,
   WDEV_NUM_MAX+1,main_dev,iot_dev,VIRTUAL_IF_NUM(ad),
   &ad->wr_iot_closed_probe,&producer,producer_generation);
 main_record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,
   WDEV_NUM_MAX+1,main_dev);
 if(exact)accepted=wr_iot_physical_stop_lifetime_begin_main(
  &ad->wr_iot_physical_lifetime,&ad->wr_iot_transition,
  &ad->wr_iot_main_recovery,main_record,main_dev);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!accepted)return -EAGAIN;
 *serial=accepted;return 0;
}
