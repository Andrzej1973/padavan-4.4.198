/* MacTableDeleteEntry already holds MacTabLock. Match the current WDS
 * registration before any timer/vendor mutation; do not wait under locks. */
#ifdef WDS_SUPPORT
 if (IS_ENTRY_WDS(pEntry)) {
  ULONG wr_flags;
  UINT wr_slot;
  INT wr_allowed = 0;
  /* The vendor function otherwise reports TRUE on address mismatch and
   * runs timer/vendor side effects before its later address comparison. */
  if (!pAddr || !MAC_ADDR_EQUAL(pEntry->Addr, pAddr)) {
   NdisReleaseSpinLock(&pAd->MacTabLock);
   return FALSE;
  }
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, wr_flags);
  if (pEntry->wdev && pEntry->wdev->if_dev) {
   for (wr_slot = 0; wr_slot < WDEV_NUM_MAX + 1; wr_slot++) {
    struct wr_iot_interface_ref *r = &pAd->wr_iot_interface_refs[wr_slot];
    if (r->device == pEntry->wdev->if_dev && r->generation &&
        r->family == WR_REF_FAMILY_WDS && r->published &&
        !r->peer_operation.active &&
        (!r->peer_operation.retirement_stage || r->peer_operation.retirement_stage == 1)) {
     wr_allowed = 1; break;
    }
   }
  }
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, wr_flags);
  if (!wr_allowed) {
   NdisReleaseSpinLock(&pAd->MacTabLock);
   return FALSE;
  }
 }
#endif
