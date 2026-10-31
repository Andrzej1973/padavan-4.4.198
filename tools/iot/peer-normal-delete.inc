/* Reserve ordinary deletion through its unlocked finishing tail. Parent reset
 * retains its own exact serial; a failed ordinary body retains table ownership.
 * This is not callback/DMA retirement or a failed-delete recovery mechanism. */
static BOOLEAN wr_iot_mac_delete_entry(RTMP_ADAPTER *pAd,USHORT wcid,UCHAR *pAddr,
 const void *device,unsigned long generation,unsigned long resume_serial,unsigned long table_serial)
{
 BOOLEAN accepted,result,ended;unsigned long serial=table_serial;
 if(!pAd||!pAddr||wcid>=MAX_LEN_OF_MAC_TABLE||wcid>=MAX_LEN_OF_TR_TABLE)return FALSE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(table_serial)accepted=wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,table_serial);
 else{
  serial=wr_iot_peer_close_executor_idle(&pAd->wr_iot_peer_close_executor)?
   wr_iot_peer_table_begin(&pAd->wr_iot_peer_table_owner):0;
  accepted=serial!=0;
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!accepted)return FALSE;
 result=wr_iot_mac_delete_entry_body(pAd,wcid,pAddr,device,generation,resume_serial,serial);
 if(table_serial)return result;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 ended=wr_iot_peer_table_finish(&pAd->wr_iot_peer_table_owner,serial,result);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return ended&&result;
}
