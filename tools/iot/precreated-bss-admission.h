/* Caller already owns adapter/peer lifetime. Snapshot rejection only: existing
 * transition/peer/RX leases must still exclude close/reset across processing.
 * No radio operation, command, allocation or readiness publication here. */
#ifndef WR_IOT_PRECREATED_BSS_ADMISSION_H
#define WR_IOT_PRECREATED_BSS_ADMISSION_H
static inline int wr_iot_precreated_bss_admitted(RTMP_ADAPTER *ad,unsigned int index)
{
 /* Preserve Main/Guest and other chipset semantics. */
 if(!IS_MT7603(ad)||index!=2)return 1;
 if(ad->ApCfg.BssidNum<3||
    ad->ApCfg.BssidNum>sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0]))return 0;
 return ad->ApCfg.MBSSID[2].wdev.if_dev&&
  RTMP_OS_NETDEV_STATE_RUNNING(ad->ApCfg.MBSSID[2].wdev.if_dev)&&
  ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq;
}
#endif
