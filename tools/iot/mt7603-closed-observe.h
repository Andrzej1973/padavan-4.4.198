/* Closed configuration snapshot only, NOT RF/FIFO/late-callback retirement.
 * Caller pins adapter/netdevices and owns a transition ticket across the whole
 * observation, revalidating it afterward. Never hold transition_lock here.
 * Buffer lifetime and network isolation release need independent evidence. */
#ifndef WR_IOT_MT7603_CLOSED_OBSERVE_H
#define WR_IOT_MT7603_CLOSED_OBSERVE_H
/* Caller owns BcnRingLock. */
static inline int wr_iot_mt7603_closed_config_locked(PRTMP_ADAPTER ad,PNET_DEV dev)
{
 UINT32 queue=0xffffffffU,tbtt=0xffffffffU;
 if(!RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_START_UP)||
    !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_INTERRUPT_IN_USE)||
    RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_RESET_IN_PROGRESS|
     fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RADIO_OFF|fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET)||
    ad->ApCfg.BssidNum<3||ad->ApCfg.BssidNum>sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0])||
    ad->ApCfg.MBSSID[0].wdev.if_dev!=ad->net_dev||!netif_running(ad->net_dev)||
    !ad->ApCfg.MBSSID[0].bcn_buf.bBcnSntReq||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=dev||netif_running(dev)||
    ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq||
    ad->wr_iot_beacon_gates[2].accepting||ad->wr_iot_beacon_gates[2].active)return 0;
 RTMP_IO_READ32(ad,ARB_BCNQCR0,&queue);
 RTMP_IO_READ32(ad,LPON_SBTOR1+4,&tbtt);
 return queue!=0xffffffffU&&tbtt!=0xffffffffU&&(queue&1U)&&
  !(queue&(1U<<17))&&!(tbtt&(TBTT0_n_INT_EN|PRE_TBTT0_n_INT_EN))&&
  !RTMP_TEST_FLAG(ad,fRTMP_ADAPTER_HALT_IN_PROGRESS|fRTMP_ADAPTER_RESET_IN_PROGRESS|
   fRTMP_ADAPTER_NIC_NOT_EXIST|fRTMP_ADAPTER_RADIO_OFF|fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET);
}
static inline int wr_iot_mt7603_closed_config_observed(PRTMP_ADAPTER ad,PNET_DEV dev)
{
 unsigned long generation;int observed;
 if(!ad||!dev||!ad->net_dev||!IS_MT7603(ad))return 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 observed=wr_iot_mt7603_closed_config_locked(ad,dev);
 generation=ad->wr_iot_beacon_gates[2].generation;
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 if(!observed)return 0;
 /* Each existing outstanding helper acquires its own ring lock. */
 if(WrBeaconDmaOutstanding(ad,2)!=0||WrBeaconTxSOutstanding(ad,2)!=0)return 0;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 observed=ad->wr_iot_beacon_gates[2].generation==generation&&
  wr_iot_mt7603_closed_config_locked(ad,dev);
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return observed;
}
#endif
