/* Staged synchronous finish-to-recovery bridge. Caller holds RTNL and adapter
 * lifetime across both locked operations. No competing API enter/finish for
 * this registration can run between them. Never schedule another task's close.
 * Success also requires the synchronous extra netdev put when no recovery runs.
 * Return never proves RF/reopen safety; handoff reports -1/no transfer, 0/queued,
 * 1/retained. Neither outcome authorizes isolation or lifetime-owner retirement. */
static INT wr_iot_driver_close_finish_recover(RTMP_ADAPTER *ad,PNET_DEV dev,
 const void *task,int linux_status,int *handoff)
{
 ULONG flags=0;int matched,completed;
 if(!handoff)return 0;
 *handoff=-1;
 if(!ad||!dev||!task||task!=current)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=ad->wr_iot_close_owner.active&&ad->wr_iot_close_owner.task==task&&
  ad->wr_iot_close_owner.device==dev&&!ad->wr_iot_close_owner.reference_completed&&
  !ad->wr_iot_close_owner.uncertain;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return 0;
 completed=wr_iot_driver_close_request_finish(ad,dev,task,linux_status);
 if(completed){
  /* Return only our synchronous extra hold; never invent recovery receipt. */
  if(wr_iot_driver_close_synchronous_put(ad,dev)!=0)return 0;
 }else{
  *handoff=wr_iot_driver_close_recovery_submit(ad,dev);
  /* Match the existing MBSS handoff: a retained worker needs the bounded
   * retry/poll caller as well. Failure never reverses accepted ownership. */
  if(*handoff>=0&&wr_iot_mbss_poll_schedule(ad)!=0)*handoff=1;
 }
 return completed;
}
