/* MacTabLock held; failed insertion is unpublished and has a separate owner.
 * Ordinary deletion must not release its timers or make its WCID reusable. */
 if (tr_entry->wr_iot_setup_observed && tr_entry->wr_iot_setup_result != 0) {
  NdisReleaseSpinLock(&pAd->MacTabLock);
  return FALSE;
 }
