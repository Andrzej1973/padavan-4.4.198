/* Candidate MT7603 configuration observer, not RF/client proof.
 * Driver types/macros must precede this header. Caller owns VERIFY ticket and
 * pins adapter/netdevices; no transition lock is held here. All mutators must
 * participate in shared admission before this can authorize BSS_UP. */
#ifndef WR_IOT_MT7603_MAIN_OBSERVE_H
#define WR_IOT_MT7603_MAIN_OBSERVE_H
static inline int wr_iot_mt7603_main_config_observed(PRTMP_ADAPTER ad){
 UINT32 value=0xffffffffU;
 int observed=0;
 if(!ad||!IS_MT7603(ad)||!ad->net_dev)return 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_START_UP)&&
    RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_INTERRUPT_IN_USE)&&
    !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_HALT_IN_PROGRESS|
       fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_NIC_NOT_EXIST|
       fRTMP_ADAPTER_RADIO_OFF|fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET)&&
    ad->ApCfg.BssidNum>=3&&
    ad->ApCfg.BssidNum<=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0])&&
    ad->ApCfg.MBSSID[0].wdev.if_dev==ad->net_dev&&netif_running(ad->net_dev)&&
    ad->ApCfg.MBSSID[0].bcn_buf.bBcnSntReq&&
    ad->ApCfg.MBSSID[2].wdev.if_dev&&
    !netif_running(ad->ApCfg.MBSSID[2].wdev.if_dev)&&
    !ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq){
  RTMP_IO_READ32(ad,ARB_BCNQCR0,&value);
  observed=value!=0xffffffffU&&(value&1U)&&!(value&(1U<<2));
  if(RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_HALT_IN_PROGRESS|
       fRTMP_ADAPTER_RESET_IN_PROGRESS|fRTMP_ADAPTER_NIC_NOT_EXIST|
       fRTMP_ADAPTER_RADIO_OFF|fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET))observed=0;
 }
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return observed;
}
#endif
