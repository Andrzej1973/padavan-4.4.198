/* Whole public insertion, including the unlocked TX-burst tail. Caller pins
 * adapter/wdev lifetime; startup-ticket insertion has its separate lease. */
MAC_TABLE_ENTRY *MacTableInsertEntry(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,UINT32 ent_type,UCHAR OpMode,BOOLEAN CleanAll)
{
 MAC_TABLE_ENTRY *result;BOOLEAN entered,ended;
 if(!pAd||!pAddr||!wdev)return NULL;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 entered=wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor) &&
  wr_iot_peer_table_transaction_enter(&pAd->wr_iot_peer_table_owner);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!entered)return NULL;
 result=wr_iot_mac_insert_entry(pAd,pAddr,wdev,ent_type,OpMode,CleanAll,NULL,0);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 ended=wr_iot_peer_table_transaction_leave(&pAd->wr_iot_peer_table_owner);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return ended?result:NULL;
}
