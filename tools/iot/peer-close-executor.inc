/* Both bodies run outside locks; the executor spans every body return. */
INT RTMPDrvClose(VOID *pAdSrc,VOID *net_dev)
{
 RTMP_ADAPTER *pAd=(RTMP_ADAPTER *)pAdSrc;
 INT result;int accepted,started;
 if(!pAd)return NDIS_STATUS_FAILURE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 accepted=wr_iot_peer_close_executor_enter(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_LEGACY,0);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!accepted)return NDIS_STATUS_FAILURE;
 result=wr_iot_legacy_close_body(pAdSrc,net_dev);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 started=pAd->wr_iot_peer_legacy_close_state==1U;
 accepted=wr_iot_peer_close_executor_leave(&pAd->wr_iot_peer_close_executor,
  WR_PEER_CLOSE_LEGACY,0,result==NDIS_STATUS_SUCCESS,started);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return accepted?result:NDIS_STATUS_FAILURE;
}
INT wr_iot_drv_close_checked(VOID *pAdSrc,VOID *net_dev,const struct wr_iot_radio_ticket *ticket)
{
 RTMP_ADAPTER *pAd=(RTMP_ADAPTER *)pAdSrc;
 INT result;int accepted,started=0;
 if(!pAd||!ticket)return NDIS_STATUS_FAILURE;
 NdisAcquireSpinLock(&pAd->MacTabLock);
 accepted=wr_iot_peer_close_executor_enter(&pAd->wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,ticket->serial);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 if(!accepted)return NDIS_STATUS_FAILURE;
 result=wr_iot_checked_close_body(pAdSrc,net_dev,ticket,&started);
 NdisAcquireSpinLock(&pAd->MacTabLock);
 accepted=wr_iot_peer_close_executor_leave(&pAd->wr_iot_peer_close_executor,
  WR_PEER_CLOSE_CHECKED,ticket->serial,result==NDIS_STATUS_SUCCESS,started);
 NdisReleaseSpinLock(&pAd->MacTabLock);
 return accepted?result:NDIS_STATUS_FAILURE;
}
