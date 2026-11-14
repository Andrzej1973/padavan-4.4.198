/* Dormant Linux ARM admission, not an endpoint or physical completion proof.
 * Caller holds RTNL and adapter/main-netdev/module lifetime. It must either
 * publish the physical record/pins or unwind this lifetime before returning.
 * Valid only with the verified immutable no-host ra2 beacon configuration. */
#ifndef WR_IOT_RA2_NO_HOST_MODE
#error "Physical ARM admission requires verified immutable ra2 no-host mode"
#endif
#include "physical-stop-prior-close.h"
#include "physical-stop-lifetime.h"
#include "physical-stop-record.h"
static INT __attribute__((unused)) wr_iot_physical_stop_arm_admit(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_stop_request *request,unsigned long *serial)
{
 struct wr_iot_beacon_producer_gate producer;
 struct wr_iot_interface_ref *main_record;
 PNET_DEV iot_dev;
 unsigned long producer_generation,accepted=0;
 unsigned long long record_serial;ULONG flags=0;
 int exact;
 if(!ad||!main_dev||!serial||!wr_iot_physical_stop_request_valid(request)||
    request->action!=WR_STOP_ARM)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 /* RTNL serializes record publication/terminal cleanup. Read its own lock;
  * never nest MacTabLock with transition or beacon locks. */
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 exact=ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&
       !ad->wr_iot_physical_stop.task;
 record_serial=ad->wr_iot_physical_stop.serial;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!exact)return -EBUSY;
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
 if(accepted)ad->wr_iot_physical_lifetime.arm_record_serial=record_serial;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!accepted)return -EAGAIN;
 *serial=accepted;return 0;
}

/* Only the synchronous ARM issuer may use this before record publication.
 * A changed record serial detects publish+detach as well as a live record.
 * Unpublished local references remain owned by the caller's outer lifetime. */
static INT __attribute__((unused)) wr_iot_physical_stop_arm_abort_unpublished(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,unsigned long serial)
{
 struct wr_iot_physical_stop_lifetime *s;
 struct wr_iot_interface_ref *record;
 unsigned long long record_serial;ULONG flags=0;int idle,ended=0;
 if(!ad||!main_dev||!serial)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 idle=ad->wr_iot_physical_stop.phase==WR_PHYS_STOP_IDLE&&
      !ad->wr_iot_physical_stop.task;
 record_serial=ad->wr_iot_physical_stop.serial;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!idle)return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 s=&ad->wr_iot_physical_lifetime;
 record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev);
 if(s->active&&s->serial==serial&&s->main_device==main_dev&&
    !s->main_ticket_valid&&s->arm_record_serial==record_serial&&
    ad->wr_iot_main_recovery.phase==WR_MAIN_OWNER_IDLE&&
    !ad->wr_iot_main_recovery.deferred_owners&&record&&
    record->generation==s->main_generation&&record->last_token==s->main_open_token&&
    record->published&&!record->removing&&record->family==WR_REF_FAMILY_MAIN&&
    ad->wr_iot_transition.serial==s->arm_radio_serial&&
    ad->wr_iot_transition.epoch==s->arm_radio_epoch&&
    ad->wr_iot_transition.phase==WR_RADIO_READY&&!ad->wr_iot_transition.busy&&
    ad->wr_iot_transition.main_ready&&!ad->wr_iot_transition.main_inhibited&&
    !ad->wr_iot_transition.pm_suspending&&!ad->wr_iot_transition.pm_suspended&&
    !ad->wr_iot_transition.retiring&&!ad->wr_iot_transition.reset_pending)
  ended=wr_iot_physical_stop_lifetime_end(s,serial,1,1);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ended?0:-EBUSY;
}
