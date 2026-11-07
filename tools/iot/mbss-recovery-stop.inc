/* External adapter-pinned teardown only. Caller excludes new submission and
 * another join/reaper, holds no RTNL/spinlock and is not this work callback.
 * Cancellation is not close completion; retain unfinished owner/ref storage. */
INT wr_iot_mbss_recovery_stop_join(RTMP_ADAPTER *ad)
{
 UINT slot;
 ULONG flags;
 if(!ad||wr_iot_os_join_context())return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++)
  (void)wr_iot_mbss_recovery_request_stop(&ad->wr_iot_mbss_recovery[slot]);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++)
  cancel_work_sync(&ad->wr_iot_mbss_work[slot].work);
 return wr_iot_mbss_recovery_join_completed(ad);
}
