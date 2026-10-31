/* MacTabLock held, before selecting/resetting an entry or timer. */
 if (!wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0)) {
  NdisReleaseSpinLock(&pAd->MacTabLock);
  return NULL;
 }
