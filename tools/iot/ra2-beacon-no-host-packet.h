/* Unbound pre-submit memory predicate. Caller owns BcnRingLock, the actual
 * producer ticket and adapter/netdev lifetime. Pass the DMA snapshot obtained
 * under that exclusive producer lease. Never synthesize a ticket from gate
 * fields: the original builder ticket must reach this call through the ABI.
 * This does not release DMA, submit TX or prove a reservation-free epoch. */
#ifndef WR_IOT_RA2_BEACON_NO_HOST_PACKET_H
#define WR_IOT_RA2_BEACON_NO_HOST_PACKET_H
#include "beacon-producer-gate.h"
#include "ra2-beacon-no-host-txd.h"
static inline int wr_iot_ra2_no_host_packet(RTMP_ADAPTER *ad,PNDIS_PACKET packet,
 const struct wr_iot_beacon_producer_ticket *ticket,const void *bytes,
 unsigned int length,int dma_snapshot)
{
 if(!ad||!packet||!ticket||!IS_MT7603(ad)||ad->ApCfg.BssidNum!=3||
    dma_snapshot!=0||ad->wr_iot_beacon_gates[2].active!=1||
    !wr_iot_beacon_gate_submit(&ad->wr_iot_beacon_gates[2],ticket)||
    ad->ApCfg.MBSSID[2].bcn_buf.BeaconPkt!=packet||
    !ad->ApCfg.MBSSID[2].wdev.if_dev||
    !netif_running(ad->ApCfg.MBSSID[2].wdev.if_dev)||
    !ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq||
    ad->ApCfg.MBSSID[2].bcn_buf.bcn_state!=BCN_TX_IDLE)return 0;
 if(length!=GET_OS_PKT_LEN(packet)||bytes!=GET_OS_PKT_DATAPTR(packet))return 0;
 return wr_iot_ra2_no_host_txd(bytes,length);
}
#endif
