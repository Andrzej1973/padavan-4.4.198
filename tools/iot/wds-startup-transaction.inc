/* Caller pins adapter and main device and passes explicit open identity.
 * Lease spans the entire counted WDS body, finishing tails and dev_put. */
MAC_TABLE_ENTRY *wr_iot_wds_insert_startup(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 UINT index,const struct wr_iot_peer_open_ticket *ticket)
{
 unsigned long lease;
 BOOLEAN ended;
 MAC_TABLE_ENTRY *result;
 if(!pAd||!pAddr||!ticket||index>=MAX_WDS_ENTRY)return NULL;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 lease=wr_iot_peer_open_insert_begin(&pAd->wr_iot_peer_open_owner,
  &pAd->wr_iot_peer_table_owner,ticket);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!lease)return NULL;
 result=wr_iot_wds_insert_transaction_owned(pAd,pAddr,index,2,ticket,lease);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 ended=wr_iot_peer_open_insert_end(&pAd->wr_iot_peer_open_owner,
  &pAd->wr_iot_peer_table_owner,ticket,lease);
 if(!result||!ended||!wr_iot_peer_open_matches(&pAd->wr_iot_peer_open_owner,
    &pAd->wr_iot_peer_table_owner,ticket)||
    pAd->wr_iot_peer_open_owner.phase!=WR_PEER_OPEN_STARTUP){
  (void)wr_iot_peer_open_finish(&pAd->wr_iot_peer_open_owner,
   &pAd->wr_iot_peer_table_owner,ticket,0);
  result=NULL;
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return result;
}
