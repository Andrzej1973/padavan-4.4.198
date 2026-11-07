/* RX1 + control-TX only. Data remains joined/blocked, release claim retained.
 * Caller owns main-open/bootstrap and cookie lifetime. No firmware epoch proof. */
static INT wr_iot_boot_nettask_init(RTMP_ADAPTER *pAd)
{
 POS_COOKIE cookie=(POS_COOKIE)pAd->OS_Cookie;
 ULONG flags=0;
 RTMP_NET_TASK_STRUCT *created[2];unsigned int count=0;
 int ready;
 if(!cookie||in_atomic()||irqs_disabled()||!wr_iot_mcu_boot_owned(pAd))
  return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=pAd->wr_iot_nettask_release_claimed && pAd->wr_iot_nettask_joined &&
       pAd->wr_iot_nettask_data_joined && !pAd->wr_iot_nettask_initializing &&
       !pAd->wr_iot_nettask_data_joining && !pAd->wr_iot_boot_mcu_only &&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner) &&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner);
 if(ready)pAd->wr_iot_nettask_initializing=1;
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
#ifdef OS_ABL_FUNC_SUPPORT
 if(!RTMP_OS_TASKLET_INIT(pAd,&cookie->rx1_done_task,rx1_done_tasklet,(unsigned long)pAd))goto fail;
#else
 RTMP_OS_TASKLET_INIT(pAd,&cookie->rx1_done_task,rx1_done_tasklet,(unsigned long)pAd);
#endif
 created[count++]=&cookie->rx1_done_task;
#ifdef OS_ABL_FUNC_SUPPORT
 if(!RTMP_OS_TASKLET_INIT(pAd,&cookie->hcca_dma_done_task,hcca_dma_done_tasklet,(unsigned long)pAd))goto fail;
#else
 RTMP_OS_TASKLET_INIT(pAd,&cookie->hcca_dma_done_task,hcca_dma_done_tasklet,(unsigned long)pAd);
#endif
 created[count++]=&cookie->hcca_dma_done_task;
 if(!wr_iot_mcu_boot_owned(pAd))goto fail;
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=pAd->wr_iot_nettask_initializing && pAd->wr_iot_nettask_release_claimed &&
       pAd->wr_iot_nettask_joined && pAd->wr_iot_nettask_data_joined &&
       !pAd->wr_iot_nettask_data_joining && !pAd->wr_iot_boot_mcu_only &&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner) &&
       wr_iot_tasklet_schedule_open(&pAd->wr_iot_nettask_owner,1,1);
 if(ready){
  pAd->wr_iot_boot_mcu_only=1;pAd->wr_iot_nettask_joined=0;
  pAd->wr_iot_nettask_initializing=0;
 }
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 if(ready)return NDIS_STATUS_SUCCESS;
fail:
 while(count)RTMP_OS_TASKLET_KILL(created[--count]);
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
 pAd->wr_iot_nettask_initializing=0;
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 return NDIS_STATUS_FAILURE;
}
static INT wr_iot_boot_nettask_exit(RTMP_ADAPTER *pAd)
{
 POS_COOKIE cookie=(POS_COOKIE)pAd->OS_Cookie;
 ULONG flags=0;int ready;
 if(!cookie||wr_iot_nettask_block_drain(pAd)!=NDIS_STATUS_SUCCESS)
  return NDIS_STATUS_FAILURE;
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
 ready=pAd->wr_iot_boot_mcu_only && !pAd->wr_iot_nettask_initializing &&
       pAd->wr_iot_nettask_data_joined && !pAd->wr_iot_nettask_data_joining &&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_owner) &&
       wr_iot_tasklet_schedule_may_join(&pAd->wr_iot_nettask_data_owner);
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 if(!ready)return NDIS_STATUS_FAILURE;
 RTMP_OS_TASKLET_KILL(&cookie->rx1_done_task);
 RTMP_OS_TASKLET_KILL(&cookie->hcca_dma_done_task);
 RTMP_INT_LOCK(&pAd->wr_iot_nettask_lock,flags);
 pAd->wr_iot_nettask_joined=1;pAd->wr_iot_boot_mcu_only=0;
 RTMP_INT_UNLOCK(&pAd->wr_iot_nettask_lock,flags);
 return NDIS_STATUS_SUCCESS;
}
