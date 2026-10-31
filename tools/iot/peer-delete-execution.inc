#define WR_IOT_DELETE_EXECUTION_LEASE 1
/* Synchronous execution lease, distinct from retained per-entry WDS recovery.
 * Caller pins adapter lifetime. All lease state uses MacTabLock. */
static BOOLEAN wr_iot_mac_delete_entry(RTMP_ADAPTER *pAd,USHORT wcid,UCHAR *pAddr,
 const void *device,unsigned long generation,unsigned long resume_serial,unsigned long table_serial)
{
 BOOLEAN accepted,result;
 if(!pAd||!pAddr||wcid>=MAX_LEN_OF_MAC_TABLE||wcid>=MAX_LEN_OF_TR_TABLE)return FALSE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(table_serial)accepted=!pAd->wr_iot_peer_delete_active &&
  wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,table_serial);
 else{
  accepted=!pAd->wr_iot_peer_delete_active &&
   !pAd->wr_iot_peer_table_owner.transactions &&
   wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0) &&
   wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor);
  if(accepted)pAd->wr_iot_peer_delete_active=1;
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!accepted)return FALSE;
 result=wr_iot_mac_delete_entry_body(pAd,wcid,pAddr,device,generation,resume_serial,table_serial);
 if(table_serial)return result; /* Parent reset owns its entire serial span. */
 NdisAcquireSpinLock(&pAd->MacTabLock);
 accepted=pAd->wr_iot_peer_delete_active==1;
 if(accepted)pAd->wr_iot_peer_delete_active=0;
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return accepted&&result;
}
