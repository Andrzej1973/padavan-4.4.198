/* Recovery/reference fence only, not DMA/IRQ or all-callback acceptance.
 * Actual allocation sets storage_live only after locks/work/owners/refs init.
 * Any initialized free attempt permanently retires new admission first.
 * No nested locks, waits, ref drops or worker cancellation here. */
#include "wr-iot-main-reopen-admission.h"
static BOOLEAN wr_iot_raw_recovery_free_fence(RTMP_ADAPTER *ad)
{
 ULONG flags;
 UINT slot;
 BOOLEAN ready;
 if(!ad)return FALSE;
 if(!READ_ONCE(ad->wr_iot_recovery_storage_live))return TRUE;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 wr_iot_radio_retire(&ad->wr_iot_transition);
 ready=!ad->wr_iot_registration_inflight &&
  wr_iot_main_recovery_allows_reopen(&ad->wr_iot_main_recovery,
   work_busy(&ad->wr_iot_main_recovery_work),
   work_busy(&ad->wr_iot_main_recovery_reap_work.work),
   ad->wr_iot_aux_family_retry.deferred_owners,
   work_busy(&ad->wr_iot_aux_family_retry_work)) &&
  wr_iot_mbss_recovery_storage_idle(ad->wr_iot_mbss_recovery,WDEV_NUM_MAX+1);
 for(slot=0;ready&&slot<WDEV_NUM_MAX+1;slot++){
  const struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[slot];
  if(r->device||r->published||r->removing||r->phase!=WR_REF_IDLE)ready=FALSE;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
