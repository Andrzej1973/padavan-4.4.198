/* Isolated retirement helper. Caller pins adapter/MAC entry and excludes
 * WCID reinitialization (reviewed MacTab owner), and has disabled enq/deq
 * under irq_lock. Never call with irq_lock or UAPSDEOSPLock held.
 * This joins queue mutation only, not hardware/DMA/service-period callbacks. */
INT wr_iot_uapsd_retire_queues(RTMP_ADAPTER *pAd, MAC_TABLE_ENTRY *entry)
{
 QUEUE_HEADER detached[WMM_NUM_OF_AC];
 PQUEUE_ENTRY eosp;
 ULONG flags=0;
 UINT32 ac;
 if(!pAd||!entry||entry->wcid>=MAX_LEN_OF_TR_TABLE)
  return NDIS_STATUS_FAILURE;
 UAPSD_SEM_LOCK(&pAd->UAPSDEOSPLock,flags);
 if(READ_ONCE(pAd->MacTab.tr_entry[entry->wcid].enq_cap)||
    READ_ONCE(pAd->MacTab.tr_entry[entry->wcid].deq_cap)){
  UAPSD_SEM_UNLOCK(&pAd->UAPSDEOSPLock,flags);
  return NDIS_STATUS_FAILURE;
 }
 for(ac=0;ac<WMM_NUM_OF_AC;ac++){
  detached[ac]=entry->UAPSDQueue[ac];
  InitializeQueueHeader(&entry->UAPSDQueue[ac]);
 }
 eosp=entry->pUAPSDEOSPFrame;
 entry->pUAPSDEOSPFrame=NULL;
 entry->UAPSDTxNum=0;
 entry->bAPSDFlagSPStart=0;
 entry->bAPSDFlagEOSPOK=0;
 UAPSD_SEM_UNLOCK(&pAd->UAPSDEOSPLock,flags);
 /* Detached lists are private; no shared queue lock during packet release. */
 for(ac=0;ac<WMM_NUM_OF_AC;ac++)RtmpCleanupPsQueue(pAd,&detached[ac]);
 if(eosp)RELEASE_NDIS_PACKET(pAd,QUEUE_ENTRY_TO_PACKET(eosp),NDIS_STATUS_FAILURE);
 return NDIS_STATUS_SUCCESS;
}
