/* External caller pins adapter and holds neither RTNL nor driver locks.
 * A lifecycle owner must also join this caller before releasing adapter.
 * This helper is not a periodic scheduler and is not callback-bound yet. */
INT wr_iot_mbss_recovery_poll(RTMP_ADAPTER *ad)
{
 UINT slot;
 ULONG flags;
 if(!ad||wr_iot_os_join_context())return -1;
 if(wr_iot_mbss_recovery_join_completed(ad)==0)return 0;
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++){
  PNET_DEV dev=NULL;
  unsigned long generation=0;
  struct wr_iot_mbss_recovery_owner *owner;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  owner=&ad->wr_iot_mbss_recovery[slot];
  if(owner->phase==WR_MBSS_OWNER_RETAINED&&!owner->stop_requested&&
     !owner->completed&&owner->device&&owner->generation&&
     owner->deferred_owners&&owner->attempts<3U){
   dev=(PNET_DEV)owner->device;generation=owner->generation;
   /* Reaper may release its original hold after unlock. Pin before that. */
   dev_hold(dev);
  }
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(dev){
   (void)wr_iot_mbss_recovery_retry(ad,dev,generation);
   dev_put(dev);
  }
 }
 return -1; /* Pending/retained ownership; caller must keep adapter pinned. */
}
