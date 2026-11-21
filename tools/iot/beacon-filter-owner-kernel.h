#ifndef WR_IOT_BEACON_FILTER_OWNER_KERNEL_H
#define WR_IOT_BEACON_FILTER_OWNER_KERNEL_H
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
/* Try admission only. Never hold spinlock over vendor polling or delays.
 * Callers already pin adapter lifetime. This is not reset/PCI/RF acceptance. */
static inline int wr_iot_bcn_filter_enter(RTMP_ADAPTER *ad,unsigned long *token){
 int ok;ULONG flags=0;
 if(!ad||!token)return 0;
 *token=0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ok=wr_iot_radio_tx_enter(&ad->wr_iot_transition);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ok)return 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 ok=wr_iot_beacon_filter_enter(&ad->wr_iot_beacon_filter_owner,token);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 if(!ok){
  int wake;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  wake=wr_iot_radio_tx_leave(&ad->wr_iot_transition);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(wake){
   wake_up_all(&ad->wr_iot_tx_drain_wait);
   wake_up_all(&ad->wr_iot_ticket_wait);
  }
 }
 return ok;
}
/* A recovery result is only a snapshot, never permission for future TX.
 * The ra2 caller still needs its normal producer admission. Revoke the result
 * when reset/suspend/close intent arrived while the vendor body was polling.
 * Do not acquire a second TX lease or change the shared transition machine. */
static inline int wr_iot_bcn_filter_ra2_continue(RTMP_ADAPTER *ad){
 int ready;ULONG flags=0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ready=ad->wr_iot_transition.epoch&&ad->wr_iot_transition.active_tx&&
  !ad->wr_iot_transition.retiring&&!ad->wr_iot_transition.pm_suspending&&
  !ad->wr_iot_transition.pm_suspended&&
  ad->wr_iot_transition.phase==WR_RADIO_READY&&
  ad->wr_iot_transition.main_ready&&!ad->wr_iot_transition.main_inhibited&&
  !ad->wr_iot_transition.reset_pending&&!ad->wr_iot_transition.busy;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready;
}
static inline int wr_iot_bcn_filter_leave(RTMP_ADAPTER *ad,unsigned long token){
 int ok,wake=0;ULONG flags=0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 ok=wr_iot_beacon_filter_leave(&ad->wr_iot_beacon_filter_owner,token);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 if(ok){
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  wake=wr_iot_radio_tx_leave(&ad->wr_iot_transition);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(wake){
   wake_up_all(&ad->wr_iot_tx_drain_wait);
   wake_up_all(&ad->wr_iot_ticket_wait);
  }
 }
 return ok;
}
#endif
#endif
