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
