/* Caller owns the ra2 MBSS close registration/transition. Existing SDK table
 * lock serializes station deletion. DMA cells remain with normal completion. */
#ifndef WR_IOT_RA2_SOFTWARE_OFF_H
#define WR_IOT_RA2_SOFTWARE_OFF_H
#ifdef WR_IOT_PSM_DIAG
#include <linux/ratelimit.h>
#endif
/* 0 leaves another interface unchanged; 1 completes software gating/drain;
 * -1 retains the gates after an invalid multicast ownership observation. */
static inline int wr_iot_ra2_software_stop(RTMP_ADAPTER *ad,PNET_DEV dev)
{
 unsigned int wcid,mcast;
 int result=-1;
 ULONG flags;
 STA_TR_ENTRY *traffic;
 struct wifi_dev *wdev;
 if(!ad||!dev||!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=dev)return 0;
 wdev=&ad->ApCfg.MBSSID[2].wdev;
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=FALSE;
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 NdisAcquireSpinLock(&ad->MacTabLock);
 RTMP_IRQ_LOCK(&ad->irq_lock,flags);
 for(wcid=0;wcid<MAX_LEN_OF_TR_TABLE;wcid++){
  traffic=&ad->MacTab.tr_entry[wcid];
  if(IS_ENTRY_NONE(traffic)||traffic->wcid!=wcid||
     traffic->func_tb_idx!=2||traffic->wdev!=wdev)continue;
  WRITE_ONCE(traffic->enq_cap,FALSE);
  WRITE_ONCE(traffic->deq_cap,FALSE);
  traffic->PsDeQWaitCnt=0;
  traffic->PsQIdleCount=0;
 }
 RTMP_IRQ_UNLOCK(&ad->irq_lock,flags);
 /* Station queues are drained once by the following vendor MBSS_Close ->
  * MacTableDeleteEntry -> tr_tb_reset_entry. The permanent multicast entry
  * needs its own software queue drain and will be re-enabled on MBSS open. */
 mcast=wdev->tr_tb_idx;
 if(mcast<MAX_LEN_OF_TR_TABLE && mcast==(UCHAR)mcast && mcast!=WCID_ALL){
  traffic=&ad->MacTab.tr_entry[mcast];
  if(traffic->EntryType==ENTRY_CAT_MCAST&&traffic->wcid==mcast&&
     traffic->func_tb_idx==2&&traffic->wdev==wdev){
   rtmp_tx_swq_exit(ad,mcast);
   result=1;
  }
 }
 NdisReleaseSpinLock(&ad->MacTabLock);
#ifdef WR_IOT_PSM_DIAG
 printk_ratelimited(KERN_INFO "mt76x3: ra2 software-off queues-gated\n");
#endif
 return result;
}
static inline int wr_iot_ra2_software_open(RTMP_ADAPTER *ad,PNET_DEV dev)
{
 unsigned int mcast;
 ULONG flags;
 int ready=0;
 STA_TR_ENTRY *traffic;
 struct wifi_dev *wdev;
 if(!ad||!dev)return 0;
 if(!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=dev)return 1;
 wdev=&ad->ApCfg.MBSSID[2].wdev;
 mcast=wdev->tr_tb_idx;
 if(mcast>=MAX_LEN_OF_TR_TABLE || mcast!=(UCHAR)mcast || mcast==WCID_ALL)return 0;
 NdisAcquireSpinLock(&ad->MacTabLock);
 RTMP_IRQ_LOCK(&ad->irq_lock,flags);
 traffic=&ad->MacTab.tr_entry[mcast];
 if(traffic->EntryType==ENTRY_CAT_MCAST&&traffic->wcid==mcast&&
    traffic->func_tb_idx==2&&traffic->wdev==wdev){
  ready=1;
  WRITE_ONCE(traffic->enq_cap,TRUE);
  WRITE_ONCE(traffic->deq_cap,TRUE);
  traffic->PsDeQWaitCnt=0;
  traffic->PsQIdleCount=0;
 }
 RTMP_IRQ_UNLOCK(&ad->irq_lock,flags);
 NdisReleaseSpinLock(&ad->MacTabLock);
 return ready;
}
#endif
