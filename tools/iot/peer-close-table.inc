/* Adapter-pinned close only; no waiting under MacTabLock. Not a DMA/callback
 * retirement proof. This serial survives retry and clearing of MacTab. */
static BOOLEAN wr_iot_peer_close_hold(RTMP_ADAPTER *pAd)
{
 UINT i;
 unsigned long serial;
 BOOLEAN valid=FALSE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(pAd->wr_iot_peer_close_serial){
  valid=wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,pAd->wr_iot_peer_close_serial);
  goto done;
 }
 if(!wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0)||
    pAd->wr_iot_peer_table_owner.transactions||pAd->MacTab.Size)goto done;
 for(i=1;i<MAX_LEN_OF_MAC_TABLE;i++)if(!IS_ENTRY_NONE(&pAd->MacTab.Content[i]))goto done;
 for(i=1;i<MAX_LEN_OF_TR_TABLE;i++)
  if(pAd->MacTab.tr_entry[i].wr_iot_setup_observed &&
     pAd->MacTab.tr_entry[i].wr_iot_setup_result!=0)goto done;
 serial=wr_iot_peer_table_begin(&pAd->wr_iot_peer_table_owner);
 if(serial){pAd->wr_iot_peer_close_serial=serial;valid=TRUE;}
done:
 NdisReleaseSpinLock(&pAd->MacTabLock);return valid;
}
static BOOLEAN wr_iot_peer_close_clear(RTMP_ADAPTER *pAd)
{
 BOOLEAN valid;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 valid=pAd->wr_iot_peer_close_serial &&
  wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,pAd->wr_iot_peer_close_serial) &&
  !pAd->wr_iot_peer_table_owner.transactions;
 if(valid)NdisZeroMemory(&pAd->MacTab,sizeof(MAC_TABLE));
 NdisReleaseSpinLock(&pAd->MacTabLock);return valid;
}
static BOOLEAN wr_iot_peer_close_finish(RTMP_ADAPTER *pAd)
{
 BOOLEAN valid;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 valid=pAd->wr_iot_peer_close_serial &&
  wr_iot_peer_table_close_seal(&pAd->wr_iot_peer_table_owner,pAd->wr_iot_peer_close_serial);
 if(valid)pAd->wr_iot_peer_close_serial=0;
 NdisReleaseSpinLock(&pAd->MacTabLock);return valid;
}
