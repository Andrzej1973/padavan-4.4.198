/* MacTabLock held. Preserve the disabled WDS entry after any checked hardware
 * refusal; prior timer/BA/queue effects make blind replay unsafe. */
#if defined(MT_MAC) && defined(WDS_SUPPORT)
 if (IS_ENTRY_WDS(pEntry)) {
  INT wr_result;
  /* Never narrow a WCID into the hardware's ALL-entries sentinel. */
  wr_result = wcid >= WCID_ALL ? WR_IOT_WCID_NOT_WRITTEN :
      wr_iot_delete_wcid_checked(pAd, (UCHAR)wcid);
  wr_iot_wds_record_hardware_delete(pAd, pEntry, wcid, wr_result);
  if (wr_result != WR_IOT_WCID_APPLIED) {
   NdisReleaseSpinLock(&pAd->MacTabLock);
   return FALSE;
  }
 } else
#endif
 {
  RTMP_STA_ENTRY_MAC_RESET(pAd, wcid);
 }
