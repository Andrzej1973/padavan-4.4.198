/* Caller pins adapter. All latch access uses MacTabLock. Failure retains the
 * latch; only a completed close followed by admitted main-open clears it. */
static INT wr_iot_peer_legacy_close_begin(RTMP_ADAPTER *pAd)
{
 INT result=0;
 if(!pAd)return 0;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(pAd->wr_iot_peer_legacy_close_state==1U)goto done;
 if(pAd->wr_iot_peer_table_owner.closed){result=2;goto done;}
 if(pAd->wr_iot_peer_legacy_close_state ||
    !wr_iot_peer_table_allows(&pAd->wr_iot_peer_table_owner,0) ||
    pAd->wr_iot_peer_table_owner.transactions)goto done;
 pAd->wr_iot_peer_legacy_close_state=1U;result=1;
done:
 NdisReleaseSpinLock(&pAd->MacTabLock);return result;
}
static BOOLEAN wr_iot_peer_legacy_close_finish(RTMP_ADAPTER *pAd)
{
 BOOLEAN result=FALSE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 if(pAd->wr_iot_peer_legacy_close_state==1U &&
    pAd->wr_iot_peer_table_owner.closed && !pAd->wr_iot_peer_close_serial){
  pAd->wr_iot_peer_legacy_close_state=2U;result=TRUE;
 }
 NdisReleaseSpinLock(&pAd->MacTabLock);return result;
}
