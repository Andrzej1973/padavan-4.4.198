/* MacTabLock held. Ordinary calls have no ticket or lease. Startup calls
 * require exact owner/lease and WDS type; no ambient owner bypass exists. */
 if (wr_open_ticket || wr_open_lease) {
  if (!wr_open_ticket || !wr_open_lease || ent_type!=ENTRY_WDS ||
      !wr_iot_peer_open_insert_admit(&pAd->wr_iot_peer_open_owner,
       &pAd->wr_iot_peer_table_owner,wr_open_ticket,wr_open_lease)) {
   NdisReleaseSpinLock(&pAd->MacTabLock);return NULL;
  }
 } else if (!wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0)) {
  NdisReleaseSpinLock(&pAd->MacTabLock);return NULL;
 }
