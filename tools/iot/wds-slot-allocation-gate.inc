/* WdsEntryAlloc holds WdsTabLock. Runtime netdev identity is checked before
 * Valid/address/size mutation. Pre-netdev configuration parsing stays intact. */
 if (wds_entry->wdev.if_dev) {
  ULONG wr_flags;
  UINT wr_slot;
  INT wr_allowed = 0;
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, wr_flags);
  for (wr_slot = 0; wr_slot < WDEV_NUM_MAX + 1; wr_slot++) {
   struct wr_iot_interface_ref *r = &pAd->wr_iot_interface_refs[wr_slot];
   if (r->device == wds_entry->wdev.if_dev && r->generation && r->published &&
       r->family == WR_REF_FAMILY_WDS && !r->removing && !r->peer_operation.removing) {
    wr_allowed = 1; break;
   }
  }
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, wr_flags);
  if (!wr_allowed) continue;
 }
