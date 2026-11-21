/* Candidate only. Caller pins adapter/wdev lifetime and must separately block
 * new WDS insertion/reinitialization. This closes current peer queues; it does
 * not join DMA, RX, callbacks or certify retirement. Never call with MAC/IRQ
 * locks held. Existing deletion establishes MacTabLock -> irq_lock ordering. */
INT wr_iot_wds_block_peer_admission(RTMP_ADAPTER *pAd, struct wifi_dev *wdev)
{
 UINT i;
 ULONG flags;
 if (!pAd || !wdev) return NDIS_STATUS_FAILURE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 /* Validate the complete selection before mutating any capability. */
 for (i = 1; i < MAX_LEN_OF_MAC_TABLE; i++) {
  MAC_TABLE_ENTRY *entry = &pAd->MacTab.Content[i];
  if (!IS_ENTRY_NONE(entry) && entry->wdev == wdev &&
      (!IS_ENTRY_WDS(entry) || entry->wcid != i || i >= MAX_LEN_OF_TR_TABLE)) {
   NdisReleaseSpinLock(&pAd->MacTabLock);
   return NDIS_STATUS_FAILURE;
  }
 }
 RTMP_IRQ_LOCK(&pAd->irq_lock, flags);
 for (i = 1; i < MAX_LEN_OF_MAC_TABLE && i < MAX_LEN_OF_TR_TABLE; i++) {
  MAC_TABLE_ENTRY *entry = &pAd->MacTab.Content[i];
  if (!IS_ENTRY_NONE(entry) && entry->wdev == wdev) {
   WRITE_ONCE(pAd->MacTab.tr_entry[i].enq_cap, FALSE);
   WRITE_ONCE(pAd->MacTab.tr_entry[i].deq_cap, FALSE);
  }
 }
 RTMP_IRQ_UNLOCK(&pAd->irq_lock, flags);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return NDIS_STATUS_SUCCESS;
}
