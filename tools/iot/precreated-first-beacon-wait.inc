/* Synchronous isolated OPEN wait. RTNL pins adapter/netdev and the existing
 * API owner retains configuration ownership. No transition/ring lock spans
 * sleep. Failure retains the live reference for checked recovery; never call
 * global refresh, physical restart or dev_close as an unproven rollback. */
#ifndef WR_IOT_HOST_TEST
#include <linux/jiffies.h>
#include <linux/preempt.h>
#endif
#include "precreated-first-beacon-kernel.h"
static inline int wr_iot_first_beacon_try_arm(RTMP_ADAPTER *ad,
 struct wr_iot_first_beacon_identity *id)
{
 int armed;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 if(!id->request_generation&&ad->wr_iot_first_beacon.last_request!=~0ULL)
  id->request_generation=ad->wr_iot_first_beacon.last_request+1;
 if(!ad->wr_iot_first_beacon.pending)
  id->producer_generation=ad->wr_iot_beacon_gates[2].generation;
 armed=(ad->wr_iot_first_beacon.pending&&
        wr_iot_first_beacon_identity_equal(&ad->wr_iot_first_beacon.identity,id))||
       wr_iot_first_beacon_arm_locked(ad,id,1);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return armed;
}
static inline int wr_iot_first_beacon_wait_ready(RTMP_ADAPTER *ad,
 const struct wr_iot_first_beacon_identity *id)
{
 int ready;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 ready=wr_iot_first_beacon_ready(&ad->wr_iot_first_beacon,id);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return ready;
}
static inline INT wr_iot_driver_first_beacon_wait(RTMP_ADAPTER *ad,PNET_DEV dev,
 unsigned int timeout_ms)
{
 struct wr_iot_virtual_open_claim before={0},after={0};
 struct wr_iot_first_beacon_identity id={0};
 ULONG flags=0;long remaining;int owned=0,ready=0;
 if(!ad||!dev||!timeout_ms||timeout_ms>3000)return -EINVAL;
 if(in_atomic()||irqs_disabled())goto uncertain;
 if(!wr_iot_driver_first_beacon_owner_snapshot(ad,dev,&before))goto uncertain;
 id.device=dev;id.netdev_generation=before.generation;
 id.radio_epoch=before.epoch;id.open_serial=before.serial;
 remaining=msecs_to_jiffies(timeout_ms);if(remaining<1)remaining=1;
 /* Existing producer-end wakes the same queue after its exclusive pin ends.
  * Spend one shared budget waiting for idle/arm and subsequent publication. */
 remaining=wait_event_timeout(ad->wr_iot_beacon_wait,
  wr_iot_first_beacon_try_arm(ad,&id),remaining);
 if(remaining>0)
  remaining=wait_event_timeout(ad->wr_iot_beacon_wait,
   wr_iot_first_beacon_wait_ready(ad,&id),remaining);
 if(remaining>0&&wr_iot_driver_first_beacon_owner_snapshot(ad,dev,&after))
  owned=after.device==before.device&&after.generation==before.generation&&
   after.epoch==before.epoch&&after.serial==before.serial&&
   after.operation==before.operation;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 owned=owned&&ad->wr_iot_beacon_gates[2].accepting&&
       ad->wr_iot_beacon_gates[2].generation==id.producer_generation;
 if(remaining>0)
  ready=wr_iot_first_beacon_finish(&ad->wr_iot_first_beacon,&id,owned);
 else wr_iot_first_beacon_expire(&ad->wr_iot_first_beacon,&id);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 if(ready)return 0;
uncertain:
 /* Poison only this still-owned task/device, never a newer operation. The
  * existing leave path keeps recovery identity and does not export success. */
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->wr_iot_driver_owner.active&&ad->wr_iot_driver_owner.task==current&&
    ad->wr_iot_driver_owner.claim.device==dev&&
    (!id.open_serial||ad->wr_iot_driver_owner.claim.serial==id.open_serial)){
  ad->wr_iot_driver_owner.poisoned=1;ad->wr_iot_control_poisoned=1;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return -EUCLEAN;
}
