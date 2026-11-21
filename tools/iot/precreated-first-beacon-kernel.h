/* Isolated candidate binding. Include after rt_config.h; caller holds
 * BcnRingLock. Adapter/netdev and current configuration lease stay pinned.
 * Capture occurs under the exclusive ra2 producer pin, before frame building.
 * Publication hook runs only after checked descriptor/CIDX publication.
 * Neither hook proves DMA completion, RF delivery, or late-TxS retirement. */
#ifndef WR_IOT_FIRST_BEACON_KERNEL_H
#define WR_IOT_FIRST_BEACON_KERNEL_H
#include "precreated-first-beacon.h"
static inline int wr_iot_first_beacon_arm_locked(RTMP_ADAPTER *ad,
 const struct wr_iot_first_beacon_identity *id,int current_owner)
{
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 struct wr_iot_beacon_producer_gate *g;
 if(!ad||!IS_MT7603(ad)||ad->chipCap.hif_type!=HIF_MT||
    ad->ApCfg.BssidNum!=3||current_owner!=1||
    !wr_iot_first_beacon_identity_valid(id)||
    id->device!=ad->ApCfg.MBSSID[2].wdev.if_dev)return 0;
 g=&ad->wr_iot_beacon_gates[2];
 if(g->active||!g->accepting||g->generation!=id->producer_generation)return 0;
 return wr_iot_first_beacon_arm(&ad->wr_iot_first_beacon,id);
#else
 (void)ad;(void)id;(void)current_owner;return 0;
#endif
}
static inline void wr_iot_first_beacon_capture_locked(RTMP_ADAPTER *ad,
 int bss,unsigned long generation)
{
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 struct wr_iot_first_beacon_identity empty={0};
 struct wr_iot_beacon_producer_gate *g;
 if(!ad||bss!=2)return;
 ad->wr_iot_first_beacon_capture=empty;
 g=&ad->wr_iot_beacon_gates[2];
 if(!IS_MT7603(ad)||ad->chipCap.hif_type!=HIF_MT||ad->ApCfg.BssidNum!=3||
    !ad->wr_iot_first_beacon.pending||g->active!=1||!g->accepting||
    g->generation!=generation||
    ad->wr_iot_first_beacon.identity.producer_generation!=generation||
    ad->wr_iot_first_beacon.identity.device!=ad->ApCfg.MBSSID[2].wdev.if_dev)return;
 ad->wr_iot_first_beacon_capture=ad->wr_iot_first_beacon.identity;
#else
 (void)ad;(void)bss;(void)generation;
#endif
}
static inline int wr_iot_first_beacon_published_locked(RTMP_ADAPTER *ad,int bss)
{
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 struct wr_iot_beacon_producer_gate *g;
 if(!ad||bss!=2||!IS_MT7603(ad)||ad->chipCap.hif_type!=HIF_MT||
    ad->ApCfg.BssidNum!=3)return 0;
 g=&ad->wr_iot_beacon_gates[2];
 if(g->active!=1||!g->accepting||
    g->generation!=ad->wr_iot_first_beacon_capture.producer_generation||
    ad->wr_iot_first_beacon_capture.device!=ad->ApCfg.MBSSID[2].wdev.if_dev)return 0;
 return wr_iot_first_beacon_submitted(&ad->wr_iot_first_beacon,
  &ad->wr_iot_first_beacon_capture,1);
#else
 (void)ad;(void)bss;return 0;
#endif
}
#endif
