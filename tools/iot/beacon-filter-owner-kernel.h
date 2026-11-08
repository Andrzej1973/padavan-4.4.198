#ifndef WR_IOT_BEACON_FILTER_OWNER_KERNEL_H
#define WR_IOT_BEACON_FILTER_OWNER_KERNEL_H
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
/* Try admission only. Never hold spinlock over vendor polling or delays.
 * Callers already pin adapter lifetime. This is not reset/PCI/RF acceptance. */
static inline int wr_iot_bcn_filter_enter(RTMP_ADAPTER *ad,unsigned long *token){
 int ok;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 ok=wr_iot_beacon_filter_enter(&ad->wr_iot_beacon_filter_owner,token);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return ok;
}
static inline int wr_iot_bcn_filter_leave(RTMP_ADAPTER *ad,unsigned long token){
 int ok;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 ok=wr_iot_beacon_filter_leave(&ad->wr_iot_beacon_filter_owner,token);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return ok;
}
#endif
#endif
