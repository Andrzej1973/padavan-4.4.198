/* Retry caller pins adapter and the original registration. No new netdev or
 * module reference is acquired: retained ownership already holds both. */
INT wr_iot_mbss_recovery_retry(RTMP_ADAPTER *ad,PNET_DEV dev,
 unsigned long generation)
{
 struct wr_iot_interface_ref *record;
 struct wr_iot_mbss_recovery_owner *owner;
 ULONG flags;UINT slot;int scheduled=0;
 if(!ad||!dev||!generation)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_mbss_submission_enter(&ad->wr_iot_mbss_reaper_gate))goto out;
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation);
 if(!record||!record->published||record->removing||record->removal_stage||
    record->family!=WR_REF_FAMILY_MBSS)goto leave;
 slot=(UINT)(record-ad->wr_iot_interface_refs);
 owner=&ad->wr_iot_mbss_recovery[slot];
 if(owner->device!=dev||owner->generation!=generation||
    owner->open_token!=record->last_token||
    work_busy(&ad->wr_iot_mbss_work[slot].work)||
    (ad->wr_iot_transition.retiring&&
     ad->wr_iot_pci_retirement.phase!=WR_PCI_RETIRE_DRAINING))goto leave;
 if(wr_iot_mbss_recovery_requeue(owner,3U)){
  scheduled=schedule_work(&ad->wr_iot_mbss_work[slot].work);
  if(!scheduled)owner->phase=WR_MBSS_OWNER_RETAINED;
 }
leave:
 (void)wr_iot_mbss_submission_leave(&ad->wr_iot_mbss_reaper_gate);
out:
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return scheduled?0:-1;
}
/* Called under RTNL with adapter/module lifetime already pinned by acquired
 * open. No callback uses this entry until ordinary reaping is installed.
 * On accepted ownership, netdev hold survives even a schedule refusal.
 * Caller must keep the original module pin until checked close consumes it. */
/* Result: -1 rejects ownership; 0 accepts and schedules; 1 accepts but retains
 * after schedule refusal. Both nonnegative results transfer the close duty
 * to the owner, so the caller must not release the original open/module pin. */
INT wr_iot_mbss_recovery_submit(RTMP_ADAPTER *ad,PNET_DEV dev,
 unsigned long generation)
{
 struct wr_iot_interface_ref *record;
 struct wr_iot_mbss_recovery_owner *owner;
 ULONG flags;
 UINT slot;
 int entered,queued=0,scheduled=0;
 if(!ad||!dev||!generation)return -1;
 dev_hold(dev);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 entered=wr_iot_mbss_submission_enter(&ad->wr_iot_mbss_reaper_gate);
 if(!entered)goto out;
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation);
 if(!record||record->removing||record->family!=WR_REF_FAMILY_MBSS||
    (ad->wr_iot_transition.retiring&&
     ad->wr_iot_pci_retirement.phase!=WR_PCI_RETIRE_DRAINING))goto leave;
 slot=(UINT)(record-ad->wr_iot_interface_refs);
 owner=&ad->wr_iot_mbss_recovery[slot];
 if(work_busy(&ad->wr_iot_mbss_work[slot].work))goto leave;
 queued=wr_iot_mbss_recovery_queue(owner,record,&ad->wr_iot_transition,
   WR_MBSS_RECOVERY_OPEN_ACQUIRED,NULL,1,1);
 if(queued){
  scheduled=schedule_work(&ad->wr_iot_mbss_work[slot].work);
  /* schedule_work(FALSE) after ownership admission cannot justify dropping
   * the lifetime fence. Leave an explicit retained owner for external retry. */
  if(!scheduled)owner->phase=WR_MBSS_OWNER_RETAINED;
 }
leave:
 (void)wr_iot_mbss_submission_leave(&ad->wr_iot_mbss_reaper_gate);
out:
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!queued)dev_put(dev);
 return queued?(scheduled?0:1):-1;
}
