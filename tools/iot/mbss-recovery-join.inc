/* External teardown/reaper only: caller pins adapter, excludes another reaper
 * and future admission for these slots, holds no RTNL/driver lock, and is not
 * one of the joined work callbacks. No automatic retry or physical proof. */
INT wr_iot_mbss_recovery_join_completed(RTMP_ADAPTER *ad)
{
 UINT slot;
 ULONG flags;
 int ready=1;
 if(!ad||wr_iot_os_join_context())return -1;
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++){
  PNET_DEV dev=NULL;
  struct wr_iot_mbss_recovery_owner *owner;
  flush_work(&ad->wr_iot_mbss_work[slot].work);
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  owner=&ad->wr_iot_mbss_recovery[slot];
  if(!work_busy(&ad->wr_iot_mbss_work[slot].work)&&owner->completed){
   const struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[slot];
   /* Completion belongs to this original registration, never a reused slot. */
   if(r->device==owner->device&&r->generation==owner->generation&&
      r->last_token==owner->open_token&&r->family==WR_REF_FAMILY_MBSS&&
      r->phase==WR_REF_IDLE&&r->close_stage==4U&&
      r->close_serial==owner->close_serial&&
      wr_iot_mbss_recovery_ticket_recorded(r,&owner->close_ticket)){
    dev=(PNET_DEV)owner->device;
    if(!wr_iot_mbss_recovery_complete(owner,1))dev=NULL;
   }
  }
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(dev)dev_put(dev);
 }
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ready=wr_iot_mbss_recovery_idle_locked(ad);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return ready?0:-1;
}
