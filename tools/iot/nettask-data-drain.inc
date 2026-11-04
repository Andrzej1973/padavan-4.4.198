/* Caller pins the cookie/adapter and serializes physical joins. Only MT7603
 * RX1 and command-TX completion bypass the data gate; global close blocks all.
 * Data join is not DMA retirement and does not permit freeing AP storage. */
static int wr_iot_nettask_is_mcu(RTMP_ADAPTER *pAd,RTMP_NET_TASK_STRUCT *task)
{
#if defined(MT_MAC) && defined(RTMP_PCI_SUPPORT) && defined(CONFIG_ANDES_SUPPORT)
 POS_COOKIE cookie=(POS_COOKIE)pAd->OS_Cookie;
 return IS_MT7603(pAd)&&pAd->chipCap.hif_type==HIF_MT&&
        (task==&cookie->rx1_done_task||task==&cookie->hcca_dma_done_task);
#else
 (void)pAd;(void)task;return 0;
#endif
}
static int wr_iot_nettask_data_drained(RTMP_ADAPTER *pAd)
{
 ULONG flags=0;int ready;
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 return ready;
}
static INT wr_iot_nettask_data_block_drain(RTMP_ADAPTER *pAd)
{
 ULONG flags=0;int ready;
 if(in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
 if(pAd->wr_iot_nettask_data_joined){
  RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);return NDIS_STATUS_SUCCESS;
 }
 if(pAd->wr_iot_nettask_initializing||pAd->wr_iot_nettask_release_claimed||
    pAd->wr_iot_nettask_data_joining||pAd->wr_iot_nettask_owner.blocked){
  RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);return NDIS_STATUS_FAILURE;
 }
 pAd->wr_iot_nettask_data_joining=1;
 wr_iot_tasklet_schedule_block(&pAd->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=wait_event_timeout(pAd->wr_iot_nettask_wait,
       wr_iot_nettask_data_drained(pAd),msecs_to_jiffies(5000));
 if(!ready){
  RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
  pAd->wr_iot_nettask_data_joining=0;
  RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 }
 return ready?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
