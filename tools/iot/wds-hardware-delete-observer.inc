/* MacTabLock already held. Never acquire WdsTabLock in this path. */
#if defined(MT_MAC) && defined(WDS_SUPPORT)
static VOID wr_iot_wds_record_hardware_delete(RTMP_ADAPTER *pAd,
 MAC_TABLE_ENTRY *peer, UINT wcid, INT result)
{
 ULONG flags;
 UINT i;
 if (!peer->wdev || !peer->wdev->if_dev) return;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 for (i = 0; i < WDEV_NUM_MAX + 1; i++) {
  struct wr_iot_interface_ref *r = &pAd->wr_iot_interface_refs[i];
  struct wr_iot_wds_peer_operation *owner = &r->peer_operation;
  if (r->device == peer->wdev->if_dev && r->published &&
      r->family == WR_REF_FAMILY_WDS &&
      wr_iot_wds_retirement_matches(owner, r->device, r->generation,
          owner->retirement_serial, owner->retirement_index, wcid, peer->Addr)) {
   (void)wr_iot_wds_retirement_hardware_result(owner, owner->retirement_serial, result);
   break;
  }
 }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
}
#endif
