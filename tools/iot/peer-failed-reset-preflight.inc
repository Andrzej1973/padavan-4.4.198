/* Observation only, not a reset transaction. No waiting under MacTabLock.
 * Caller must still serialize table mutation before treating reset as safe. */
static BOOLEAN wr_iot_reset_has_failed_setup(RTMP_ADAPTER *pAd,struct wifi_dev *scope)
{
 UINT i;
 BOOLEAN failed = FALSE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 for (i = 1; i < MAX_LEN_OF_MAC_TABLE && i < MAX_LEN_OF_TR_TABLE; i++) {
  MAC_TABLE_ENTRY *entry = &pAd->MacTab.Content[i];
  STA_TR_ENTRY *tr = &pAd->MacTab.tr_entry[i];
  if (tr->wr_iot_setup_observed && tr->wr_iot_setup_result != 0 &&
      (!scope || !entry->wdev || entry->wdev == scope)) {
   failed = TRUE;break;
  }
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return failed;
}
