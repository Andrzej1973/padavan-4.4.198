/* Caller holds MacTabLock. Removal marks under transition lock, drops it,
 * then takes MacTabLock to close peers. No transition -> MAC nested edge. */
#ifdef WDS_SUPPORT
 if (ent_type == ENTRY_WDS) {
  UINT wr_slot;
  ULONG wr_flags;
  INT wr_allowed = 0;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, wr_flags);
  if (wdev && wdev->if_dev && !pAd->wr_iot_transition.retiring &&
      !pAd->wr_iot_transition.pm_suspending && !pAd->wr_iot_transition.pm_suspended) {
   for (wr_slot = 0; wr_slot < WDEV_NUM_MAX + 1; wr_slot++) {
    struct wr_iot_interface_ref *wr_record = &pAd->wr_iot_interface_refs[wr_slot];
    if (wr_record->device == wdev->if_dev && wr_record->generation &&
        wr_record->family == WR_REF_FAMILY_WDS && wr_record->published &&
        !wr_record->removing) {
     wr_allowed = 1;
     break;
    }
   }
  }
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, wr_flags);
  if (!wr_allowed) {
   NdisReleaseSpinLock(&pAd->MacTabLock);
   return NULL;
  }
 }
#endif
