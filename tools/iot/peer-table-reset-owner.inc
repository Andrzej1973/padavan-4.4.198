/* Preflight and reservation are one MacTabLock critical section. Scope only
 * selects the preflight entries; ownership excludes the whole table. */
static unsigned long wr_iot_peer_reset_begin(RTMP_ADAPTER *pAd,struct wifi_dev *scope)
{
 UINT i;
 unsigned long serial;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if (!wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0)) {
  NdisReleaseSpinLock(&pAd->MacTabLock);return 0;
 }
 for (i=1;i<MAX_LEN_OF_MAC_TABLE && i<MAX_LEN_OF_TR_TABLE;i++) {
  MAC_TABLE_ENTRY *entry=&pAd->MacTab.Content[i];
  STA_TR_ENTRY *tr=&pAd->MacTab.tr_entry[i];
  if (tr->wr_iot_setup_observed && tr->wr_iot_setup_result!=0 &&
      (!scope || !entry->wdev || entry->wdev==scope)) {
   NdisReleaseSpinLock(&pAd->MacTabLock);return 0;
  }
 }
 serial=wr_iot_peer_table_begin(&pAd->wr_iot_peer_table_owner);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return serial;
}
static BOOLEAN wr_iot_peer_reset_finish(RTMP_ADAPTER *pAd,unsigned long serial,BOOLEAN success)
{
 BOOLEAN matched;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 matched=wr_iot_peer_table_finish(&pAd->wr_iot_peer_table_owner,serial,success);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return matched && success;
}
