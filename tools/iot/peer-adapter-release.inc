/* Initialized adapter only. A terminal PCI receipt must be produced by actual
 * callback/work/DMA retirement elsewhere, not inferred here. No waits or nested
 * locks. Cold direct-free unwind is a separate, still-open contract. */
static BOOLEAN wr_iot_adapter_release_begin(RTMP_ADAPTER *pAd)
{
 ULONG flags;UINT i;unsigned int required_workers=1U;BOOLEAN ready;
#ifdef WSC_INCLUDED
 required_workers|=2U;
#endif
 if(!pAd)return FALSE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 ready=pAd->wr_iot_pci_retirement.phase==WR_PCI_RETIRE_RELEASE_CLAIMED &&
  pAd->wr_iot_children.phase==WR_CHILD_DONE && pAd->wr_iot_transition.retiring &&
  pAd->wr_iot_transition.phase==WR_RADIO_DOWN && !pAd->wr_iot_transition.busy &&
  !pAd->wr_iot_transition.active_tx && !pAd->wr_iot_transition.reset_pending &&
  !pAd->wr_iot_transition.main_ready && pAd->wr_iot_transition.shutdown_stage==2U &&
  (pAd->wr_iot_transition.joined_workers&required_workers)==required_workers &&
  !pAd->wr_iot_registration_inflight && !pAd->wr_iot_main_recovery.deferred_owners;
 for(i=0;ready&&i<WDEV_NUM_MAX+1;i++){
  struct wr_iot_interface_ref *r=&pAd->wr_iot_interface_refs[i];
  if(r->device||r->published||r->removing||r->phase!=WR_REF_IDLE)ready=FALSE;
 }
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if(!ready)return FALSE;
 /* RELEASE_CLAIMED is terminal; no legitimate transition may revoke it.
  * Peer admission remains independent until this final short transaction. */
 NdisAcquireSpinLock(&pAd->MacTabLock);
 ready=pAd->wr_iot_peer_table_owner.closed && !pAd->wr_iot_peer_table_owner.active &&
  !pAd->wr_iot_peer_table_owner.retained && !pAd->wr_iot_peer_table_owner.poisoned &&
  !pAd->wr_iot_peer_table_owner.transactions && !pAd->wr_iot_peer_delete_active &&
  !pAd->wr_iot_peer_close_serial &&
  wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor) &&
  pAd->wr_iot_peer_open_owner.phase==WR_PEER_OPEN_IDLE &&
  !pAd->wr_iot_peer_open_owner.active_lease;
 /* Permanent software fence: never clear this on a failed free/retry. */
 if(ready)pAd->wr_iot_peer_table_owner.poisoned=1;
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return ready;
}
