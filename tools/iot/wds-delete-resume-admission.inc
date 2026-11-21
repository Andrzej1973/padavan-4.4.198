/* Private resume arguments are accepted only with an exact saved owner.
 * MacTabLock held; do not acquire WdsTabLock in this path. */
 if (wr_resume_serial) {
#if defined(MT_MAC) && defined(WDS_SUPPORT)
  ULONG wr_flags;
  UINT wr_slot;
  if (!wr_resume_device || !wr_resume_generation || !pAddr ||
      wcid >= MAX_LEN_OF_TR_TABLE || !IS_ENTRY_WDS(pEntry) ||
      !pEntry->wdev || pEntry->wdev->if_dev != wr_resume_device ||
      !MAC_ADDR_EQUAL(pEntry->Addr, pAddr) ||
      READ_ONCE(tr_entry->enq_cap) || READ_ONCE(tr_entry->deq_cap)) {
   NdisReleaseSpinLock(&pAd->MacTabLock);return FALSE;
  }
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, wr_flags);
  for (wr_slot = 0; wr_slot < WDEV_NUM_MAX + 1; wr_slot++) {
   struct wr_iot_interface_ref *r = &pAd->wr_iot_interface_refs[wr_slot];
   if (r->device == wr_resume_device && r->generation == wr_resume_generation &&
       r->published && !r->removing && r->family == WR_REF_FAMILY_WDS &&
       r->phase == WR_REF_OWNED &&
       wr_iot_wds_retirement_claim_no_write(&r->peer_operation, wr_resume_device,
          wr_resume_generation, wr_resume_serial, r->peer_operation.retirement_index,
          wcid, pAddr)) {
    wr_resume_owner = r;break;
   }
  }
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, wr_flags);
  if (!wr_resume_owner) {NdisReleaseSpinLock(&pAd->MacTabLock);return FALSE;}
  wdev = pEntry->wdev;
  goto wr_iot_wds_hardware_checkpoint;
#else
  (void)wr_resume_device;(void)wr_resume_generation;
  NdisReleaseSpinLock(&pAd->MacTabLock);return FALSE;
#endif
 }
