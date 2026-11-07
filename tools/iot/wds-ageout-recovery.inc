/* Existing periodic WDS maintenance only; no new worker/service. Caller must
 * retain adapter lifetime. A handled return does not imply recovery succeeded. */
static BOOLEAN wr_iot_wds_recover_ageout(RTMP_ADAPTER *pAd, UINT index)
{
#if defined(MT_MAC) && defined(WDS_SUPPORT)
 struct wr_iot_interface_ref *record = NULL;
 struct wr_iot_wds_peer_operation *owner;
 RT_802_11_WDS_ENTRY *slot;
 PNET_DEV device = NULL;
 ULONG flags;
 UINT i;
 USHORT wcid = 0;
 UCHAR address[MAC_ADDR_LEN];
 unsigned long generation = 0,serial = 0;
 BOOLEAN handled = FALSE,attempt = FALSE,completed = FALSE;
 if (!pAd || index >= MAX_WDS_ENTRY) return FALSE;
 NdisAcquireSpinLock(&pAd->WdsTabLock);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 for (i = 0; i < WDEV_NUM_MAX + 1; i++) {
  struct wr_iot_interface_ref *r = &pAd->wr_iot_interface_refs[i];
  if (r->family == WR_REF_FAMILY_WDS && r->peer_operation.retirement_stage >= 2 &&
      r->peer_operation.retirement_index == index) {
   handled = TRUE;
   if (record) {record = NULL;break;} /* Ambiguous ownership: retain both. */
   record = r;
  }
 }
 if (record) {
  owner = &record->peer_operation;slot = &pAd->WdsTab.WdsEntry[index];
  device = slot->wdev.if_dev;generation = record->generation;
  serial = owner->retirement_serial;wcid = owner->retirement_wcid;
  COPY_MAC_ADDR(address, owner->retirement_address);
  if (record->device == device && record->published && !record->removing && record->phase == WR_REF_OWNED &&
      device && slot->wdev.if_dev == device && slot->Valid &&
      wcid && wcid < MAX_LEN_OF_MAC_TABLE && wcid < MAX_LEN_OF_TR_TABLE &&
      slot->MacTabMatchWCID == wcid && MAC_ADDR_EQUAL(slot->PeerWdsAddr,address) &&
      wr_iot_wds_retirement_matches(owner,device,generation,serial,index,wcid,address)) {
   if (owner->retirement_stage == 2 && owner->retirement_hardware_observed &&
       (owner->retirement_retry_observed?owner->retirement_retry_result:owner->retirement_hardware_result) == WR_IOT_WCID_NOT_WRITTEN) {
    dev_hold((struct net_device *)device);attempt = TRUE;
   }
  }
 }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 NdisReleaseSpinLock(&pAd->WdsTabLock);
 if (attempt) {
  (void)wr_iot_wds_resume_delete(pAd,wcid,address,device,generation,serial);
 }
 if (record) {
  NdisAcquireSpinLock(&pAd->WdsTabLock);
  NdisAcquireSpinLock(&pAd->MacTabLock);
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
  owner = &record->peer_operation;slot = &pAd->WdsTab.WdsEntry[index];
  if (record->device == device && record->generation == generation && record->published &&
      !record->removing && record->phase == WR_REF_OWNED &&
      owner->retirement_stage == 4 &&
      wr_iot_wds_retirement_matches(owner,device,generation,serial,index,wcid,address) &&
      wcid && wcid < MAX_LEN_OF_MAC_TABLE && wcid < MAX_LEN_OF_TR_TABLE &&
      slot->wdev.if_dev == device && slot->Valid && slot->MacTabMatchWCID == wcid &&
      MAC_ADDR_EQUAL(slot->PeerWdsAddr,address) && IS_ENTRY_NONE(&pAd->MacTab.Content[wcid]) &&
      !READ_ONCE(pAd->MacTab.tr_entry[wcid].enq_cap) && !READ_ONCE(pAd->MacTab.tr_entry[wcid].deq_cap) &&
      pAd->WdsTab.Size && pAd->wr_iot_transition.active_tx &&
      wr_iot_wds_retirement_complete(owner,serial)) {
   slot->Valid = FALSE;NdisZeroMemory(slot->PeerWdsAddr,MAC_ADDR_LEN);
   pAd->WdsTab.Size--; (void)wr_iot_radio_tx_leave(&pAd->wr_iot_transition);
   completed = TRUE;
  }
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
  NdisReleaseSpinLock(&pAd->MacTabLock);
  NdisReleaseSpinLock(&pAd->WdsTabLock);
 }
 if (completed) wake_up_all(&pAd->wr_iot_ticket_wait);
 if (attempt) dev_put((struct net_device *)device);
 return handled;
#else
 (void)pAd;(void)index;return FALSE;
#endif
}
