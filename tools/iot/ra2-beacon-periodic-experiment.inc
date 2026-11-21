/* Unbound reservation-free periodic path. Not a complete driver mode:
 * constructor, cold epoch, callback filtering and lower submission must be
 * integrated together before this replaces the tracked periodic function. */
#include "ra2-beacon-dma-window.h"
static inline int wr_iot_bcn_periodic_ready(RTMP_ADAPTER *ad, INT bss,
 struct wr_iot_beacon_producer_ticket *ticket)
{
 int dma,txs,ready;
 UINT32 high,low;
 if(!ad||!ticket)return 0;
 if(!IS_MT7603(ad)||bss!=2)return 1;
 txs=WrBeaconTxSOutstanding(ad,2);
 dma=WrBeaconDmaOutstanding(ad,2);
 if(dma!=0||txs!=0)return 0;
 AsicGetTsfTime(ad,&high,&low);
 RTMP_SEM_LOCK(&ad->BcnRingLock);
 ready=ad->ApCfg.BssidNum==3&&ad->wr_iot_beacon_gates[2].active==1&&
  wr_iot_beacon_gate_submit(&ad->wr_iot_beacon_gates[2],ticket)&&
  ad->ApCfg.MBSSID[2].wdev.if_dev&&
  netif_running(ad->ApCfg.MBSSID[2].wdev.if_dev)&&
  ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq;
 if(ready&&ad->ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_DMA_DONE)
  ready=wr_iot_ra2_beacon_prepare_next(ad,ticket,low,dma,txs);
 else if(ready)
  ready=ad->ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_IDLE;
 RTMP_SEM_UNLOCK(&ad->BcnRingLock);
 return ready;
}
