/* MacTabLock held. Queues/timers/counters already exist: preserve an unpublished
 * failed entry, never free/reuse it as though hardware could not have changed. */
#ifdef MT_MAC
 if (pAd->chipCap.hif_type == HIF_MT) {
  INT wr_result = wr_iot_update_rx_wcid_checked(pAd,pEntry->wcid,pEntry->Addr);
  tr_entry->wr_iot_setup_result = wr_result;
  tr_entry->wr_iot_setup_observed = TRUE;
  if (wr_result != WR_IOT_WCID_APPLIED) {
   ULONG wr_flags;
   RTMP_IRQ_LOCK(&pAd->irq_lock,wr_flags);
   WRITE_ONCE(tr_entry->enq_cap,FALSE);
   WRITE_ONCE(tr_entry->deq_cap,FALSE);
   RTMP_IRQ_UNLOCK(&pAd->irq_lock,wr_flags);
   NdisReleaseSpinLock(&pAd->MacTabLock);
   return NULL;
  }
 } else
#endif
 {
  RTMP_STA_ENTRY_ADD(pAd,pEntry);
 }
