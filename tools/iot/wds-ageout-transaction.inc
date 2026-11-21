/* Candidate lazy age-out. Lock order: WdsTabLock -> MacTabLock -> transition.
 * Failure after deletion keeps reservation/radio activity for future recovery;
 * this is not DMA/TxS retirement or an adapter/module lifetime proof. */
static BOOLEAN wr_iot_wds_ageout(RTMP_ADAPTER *pAd, UINT index)
{
 struct wr_iot_interface_ref *record = NULL;
 RT_802_11_WDS_ENTRY *slot;
 MAC_TABLE_ENTRY *peer;
 PNET_DEV device = NULL;
 UCHAR address[MAC_ADDR_LEN];
 USHORT wcid = 0;
 UINT i;
 ULONG flags;
 unsigned long generation = 0;
 unsigned long retirement_serial = 0;
 BOOLEAN deleted, completed = FALSE;
 if (!pAd || index >= MAX_WDS_ENTRY) return FALSE;
 NdisAcquireSpinLock(&pAd->WdsTabLock);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 slot = &pAd->WdsTab.WdsEntry[index];
 wcid = slot->MacTabMatchWCID;
 if (pAd->WdsTab.Mode != WDS_LAZY_MODE || !slot->Valid ||
     !wcid || wcid >= MAX_LEN_OF_MAC_TABLE || wcid >= MAX_LEN_OF_TR_TABLE || !pAd->WdsTab.Size)
  goto unlock_admission;
 peer = &pAd->MacTab.Content[wcid];
 device = slot->wdev.if_dev;
 if (!device || !IS_ENTRY_WDS(peer) || peer->wcid != wcid ||
     peer->wdev != &slot->wdev ||
     !MAC_ADDR_EQUAL(peer->Addr, slot->PeerWdsAddr) ||
     peer->NoDataIdleCount < MAC_TABLE_AGEOUT_TIME)
  goto unlock_admission;
 for (i = 0; i < WDEV_NUM_MAX + 1; i++) {
  struct wr_iot_interface_ref *r = &pAd->wr_iot_interface_refs[i];
  if (r->device != device || !r->published || r->removing ||
      r->family != WR_REF_FAMILY_WDS || r->phase != WR_REF_OWNED)
   continue;
  if (!wr_iot_wds_peer_operation_begin_remove(&r->peer_operation, device, r->generation))
   break;
  if (!wr_iot_radio_tx_enter(&pAd->wr_iot_transition)) {
   /* No deletion or external mutation has occurred; exact owner still locked. */
   r->peer_operation.removing = 0;
   break;
  }
  retirement_serial = wr_iot_wds_retirement_save(&r->peer_operation,
      device, r->generation, index, wcid, peer->Addr);
  if (!retirement_serial) {
   r->peer_operation.removing = 0;
   (void)wr_iot_radio_tx_leave(&pAd->wr_iot_transition);
   break;
  }
  record = r; generation = r->generation;
  COPY_MAC_ADDR(address, peer->Addr);
  dev_hold((struct net_device *)device);
  break;
 }
unlock_admission:
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 NdisReleaseSpinLock(&pAd->WdsTabLock);
 if (!record) return FALSE;

 deleted = MacTableDeleteWDSEntry(pAd, wcid, address);

 NdisAcquireSpinLock(&pAd->WdsTabLock);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, flags);
 slot = &pAd->WdsTab.WdsEntry[index];
 /* TRUE alone is insufficient: vendor deletion also returns TRUE on no-op. */
 if (deleted && record->device == device && record->generation == generation &&
     record->published && !record->removing &&
     record->peer_operation.device == device &&
     record->peer_operation.generation == generation &&
     wr_iot_wds_retirement_matches(&record->peer_operation, device, generation,
         retirement_serial, index, wcid, address) &&
     slot->wdev.if_dev == device && slot->Valid &&
     slot->MacTabMatchWCID == wcid && MAC_ADDR_EQUAL(slot->PeerWdsAddr, address) &&
     IS_ENTRY_NONE(&pAd->MacTab.Content[wcid]) && pAd->WdsTab.Size) {
  slot->Valid = FALSE;
  NdisZeroMemory(slot->PeerWdsAddr, MAC_ADDR_LEN);
  pAd->WdsTab.Size--;
  (void)wr_iot_wds_retirement_complete(&record->peer_operation, retirement_serial);
  (void)wr_iot_radio_tx_leave(&pAd->wr_iot_transition);
  completed = TRUE;
 }
 if (!completed)
  (void)wr_iot_wds_retirement_retain(&record->peer_operation, retirement_serial);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, flags);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 NdisReleaseSpinLock(&pAd->WdsTabLock);
 wake_up_all(&pAd->wr_iot_ticket_wait);
 dev_put((struct net_device *)device);
 return completed;
}

/* Lazy-mode maintenance never carries a raw MAC entry pointer across unlock.
 * The age-out helper revalidates current identity and idle threshold itself. */
static VOID wr_iot_wds_lazy_maintenance(RTMP_ADAPTER *pAd)
{
 UINT index;
 for (index = 0; index < MAX_WDS_ENTRY; index++) {
  RT_802_11_WDS_ENTRY *slot;
  MAC_TABLE_ENTRY *peer;
  USHORT wcid;
  BOOLEAN eligible = FALSE;
  NdisAcquireSpinLock(&pAd->WdsTabLock);
  NdisAcquireSpinLock(&pAd->MacTabLock);
  slot = &pAd->WdsTab.WdsEntry[index];
  wcid = slot->MacTabMatchWCID;
  if (pAd->WdsTab.Mode == WDS_LAZY_MODE && slot->Valid && wcid &&
      wcid < MAX_LEN_OF_MAC_TABLE && wcid < MAX_LEN_OF_TR_TABLE) {
   peer = &pAd->MacTab.Content[wcid];
   if (IS_ENTRY_WDS(peer) && peer->wcid == wcid &&
       peer->wdev == &slot->wdev && MAC_ADDR_EQUAL(peer->Addr, slot->PeerWdsAddr)) {
    if (peer->NoDataIdleCount < MAC_TABLE_AGEOUT_TIME)
     peer->NoDataIdleCount++;
    if (pAd->MacTab.tr_entry[wcid].NoDataIdleCount < MAC_TABLE_AGEOUT_TIME)
     pAd->MacTab.tr_entry[wcid].NoDataIdleCount++;
    eligible = peer->NoDataIdleCount >= MAC_TABLE_AGEOUT_TIME;
   }
  }
  NdisReleaseSpinLock(&pAd->MacTabLock);
  NdisReleaseSpinLock(&pAd->WdsTabLock);
  if (eligible) (void)wr_iot_wds_ageout(pAd, index);
 }
}
