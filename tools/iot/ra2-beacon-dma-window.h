/* Unbound experiment, not an RF/TxS retirement receipt. Caller owns the
 * exclusive ra2 producer ticket and BcnRingLock. DMA/TxS snapshots must have
 * been obtained under that producer lease, with no nested ring locks.
 * This predicate does not change beacon state, release packets or submit TX.
 * It may be used only with a separately established reservation-free epoch;
 * an empty current TxS ledger does not establish such an epoch by itself. */
#ifndef WR_IOT_RA2_BEACON_DMA_WINDOW_H
#define WR_IOT_RA2_BEACON_DMA_WINDOW_H
#include "beacon-producer-gate.h"
static inline int wr_iot_ra2_beacon_dma_window(RTMP_ADAPTER *ad,
 const struct wr_iot_beacon_producer_ticket *ticket,UINT32 now,
 int dma_snapshot,int txs_snapshot)
{
 UINT32 elapsed,period;
 unsigned int slot;
 if(!ad||!ticket||!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||
    dma_snapshot!=0||txs_snapshot!=0||ad->wr_iot_beacon_gates[2].active!=1||
    !wr_iot_beacon_gate_submit(&ad->wr_iot_beacon_gates[2],ticket)||
    !ad->ApCfg.MBSSID[2].wdev.if_dev||
    !netif_running(ad->ApCfg.MBSSID[2].wdev.if_dev)||
    !ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq||
    ad->ApCfg.MBSSID[2].bcn_buf.bcn_state!=BCN_TX_DMA_DONE)return 0;
 slot=(unsigned int)ad->ApCfg.MBSSID[2].timer_loop;
 if(slot>=sizeof(ad->ApCfg.MBSSID[2].WriteBcnDoneTime)/
          sizeof(ad->ApCfg.MBSSID[2].WriteBcnDoneTime[0]))return 0;
 period=(UINT32)ad->CommonCfg.BeaconPeriod;
 if(!period||period>65535U)return 0;
 elapsed=now-(UINT32)ad->ApCfg.MBSSID[2].WriteBcnDoneTime[slot];
 /* Low TSF subtraction handles a single ordinary wrap. Reject the ambiguous
  * half-range (including a backward clock/reset), never use it as completion. */
 return elapsed<0x80000000U&&elapsed>=period*1024U;
}
/* Unbound state hand-off for the same reservation-free epoch and locks.
 * This is permission for the caller's already-owned buffer rebuild only,
 * not a DMA descriptor release or evidence that RF queues are empty.
 * The normal updater records the next attempted-publication timestamp. */
static inline int wr_iot_ra2_beacon_prepare_next(RTMP_ADAPTER *ad,
 const struct wr_iot_beacon_producer_ticket *ticket,UINT32 now,
 int dma_snapshot,int txs_snapshot)
{
 if(!wr_iot_ra2_beacon_dma_window(ad,ticket,now,dma_snapshot,txs_snapshot))
  return 0;
 ad->ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_IDLE;
 return 1;
}
#endif
