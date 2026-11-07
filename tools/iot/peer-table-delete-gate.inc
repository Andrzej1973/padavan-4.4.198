/* MacTabLock held. Only the exact active reset serial may bypass reservation.
 * Normal deletion and WDS resume supply zero and must wait outside this path. */
 if (!wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,wr_table_serial) ||
     (!wr_table_serial && pAd->wr_iot_peer_table_owner.transactions)) {
  NdisReleaseSpinLock(&pAd->MacTabLock);
  return FALSE;
 }
