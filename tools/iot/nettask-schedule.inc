/* Network-cookie tasklets only. Scheduling API runs outside the dedicated
 * short IRQ-safe lock; inflight leases prevent its storage being destroyed. */
VOID wr_iot_nettask_schedule(RTMP_ADAPTER *pAd,RTMP_NET_TASK_STRUCT *task)
{
 ULONG flags;int entered;
 if(!pAd||!task)return;
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 entered=wr_iot_tasklet_schedule_enter(&pAd->wr_iot_nettask_owner);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 if(!entered)return;
 RTMP_OS_TASKLET_SCHE(task);
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 (void)wr_iot_tasklet_schedule_leave(&pAd->wr_iot_nettask_owner);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 wake_up_all(&pAd->wr_iot_nettask_wait);
}
static int wr_iot_nettask_drained(RTMP_ADAPTER *pAd)
{
 ULONG flags;int ready;
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);return ready;
}
static INT wr_iot_nettask_block_drain(RTMP_ADAPTER *pAd)
{
 ULONG flags;
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 wr_iot_tasklet_schedule_block(&pAd->wr_iot_nettask_owner);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 if(in_atomic()||irqs_disabled())return NDIS_STATUS_FAILURE;
 if(!wait_event_timeout(pAd->wr_iot_nettask_wait,wr_iot_nettask_drained(pAd),
    msecs_to_jiffies(5000)))return NDIS_STATUS_FAILURE;
 return NDIS_STATUS_SUCCESS;
}
static INT wr_iot_nettask_open(RTMP_ADAPTER *pAd)
{
 ULONG flags;int accepted;
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 accepted=wr_iot_tasklet_schedule_open(&pAd->wr_iot_nettask_owner,1,pAd->wr_iot_nettask_joined);
 if(accepted)pAd->wr_iot_nettask_joined=0;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 return accepted?NDIS_STATUS_SUCCESS:NDIS_STATUS_FAILURE;
}
static int wr_iot_nettask_may_initialize(RTMP_ADAPTER *pAd)
{
 ULONG flags;int ready;
 RTMP_IRQ_LOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=pAd->wr_iot_nettask_joined && wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner);
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_nettask_lock,flags);return ready;
}
