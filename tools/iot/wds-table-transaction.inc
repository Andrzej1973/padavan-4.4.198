/* Wrap ALL identity paths, including configured interface-open. No MAC lock
 * spans vendor work. Synchronous enter/leave is balanced on this single path. */
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_identity(RTMP_ADAPTER *pAd,UCHAR *addr,
 UINT index,UINT mode,const struct wr_iot_peer_open_ticket *ticket,unsigned long lease,
 PNET_DEV expected_device,unsigned long expected_generation)
{
 MAC_TABLE_ENTRY *result;
 BOOLEAN entered,ended;
 if(!pAd||!addr||index>=MAX_WDS_ENTRY||(!ticket&&lease)||(ticket&&!lease))return NULL;
 if(ticket)return wr_iot_wds_insert_transaction_identity_body(pAd,addr,index,mode,
  ticket,lease,expected_device,expected_generation);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 entered=wr_iot_peer_table_transaction_enter(&pAd->wr_iot_peer_table_owner);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!entered)return NULL;
 result=wr_iot_wds_insert_transaction_identity_body(pAd,addr,index,mode,
  NULL,0,expected_device,expected_generation);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 ended=wr_iot_peer_table_transaction_leave(&pAd->wr_iot_peer_table_owner);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return ended?result:NULL;
}
