/* Adapter/netdev/module lifetime belongs to the admitted per-slot owner.
 * This work callback never acquires RTNL, never drops the netdev ref and
 * never reaps its own work_struct. External join/reap must release that ref.
 * No normal admission is installed by this layer. */
BOOLEAN wr_iot_mbss_recovery_idle_locked(RTMP_ADAPTER *ad)
{
 UINT slot;
 if(!ad||!wr_iot_mbss_recovery_storage_idle(ad->wr_iot_mbss_recovery,WDEV_NUM_MAX+1))return FALSE;
 for(slot=0;slot<WDEV_NUM_MAX+1;slot++)
  if(work_busy(&ad->wr_iot_mbss_work[slot].work))return FALSE;
 return TRUE;
}
VOID wr_iot_mbss_recovery_work_fn(struct work_struct *work)
{
#ifdef MBSS_SUPPORT
 struct wr_iot_mbss_work_context *context;
 RTMP_ADAPTER *ad;
 struct wr_iot_mbss_recovery_owner *owner;
 struct wr_iot_interface_ref *record;
 struct wr_iot_radio_ticket ticket;
 enum wr_iot_mbss_recovery_action action;
 PNET_DEV dev;
 unsigned long generation;
 ULONG flags;
 int bound,result;
 if(!work||wr_iot_os_join_context())return;
 context=container_of(work,struct wr_iot_mbss_work_context,work);
 ad=context->adapter;
 if(!ad||context->slot>=WDEV_NUM_MAX+1||context!=&ad->wr_iot_mbss_work[context->slot])return;
 owner=&ad->wr_iot_mbss_recovery[context->slot];
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(owner->attempts>=3U||!wr_iot_mbss_recovery_begin(owner)){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return;
 }
 record=&ad->wr_iot_interface_refs[context->slot];
 dev=(PNET_DEV)owner->device;generation=owner->generation;
 action=wr_iot_mbss_recovery_action(owner,record,&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad));
 if(action==WR_MBSS_RECOVERY_CONTINUE_CLOSE &&
    !wr_iot_mbss_recovery_copy_close_ticket(owner,record,&ad->wr_iot_transition,
     ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad),&ticket))
  action=WR_MBSS_RECOVERY_NONE;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(action==WR_MBSS_RECOVERY_BEGIN_CLOSE){
  if(wr_iot_mbss_begin_close(dev,&ticket,&generation)!=0)goto retain;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  record=&ad->wr_iot_interface_refs[context->slot];
  bound=generation==owner->generation &&
   wr_iot_mbss_recovery_bind_close(owner,record,&ad->wr_iot_transition,&ticket);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(!bound)goto retain;
 }else if(action!=WR_MBSS_RECOVERY_CONTINUE_CLOSE)goto retain;
 result=wr_iot_mbss_close_checked(dev,generation,&ticket);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=&ad->wr_iot_interface_refs[context->slot];
 if(result!=0)
  (void)wr_iot_mbss_recovery_record_uncertain(owner,record,&ad->wr_iot_transition);
 if(result!=0||!wr_iot_mbss_recovery_mark_completed(owner,record,&ad->wr_iot_transition))
  (void)wr_iot_mbss_recovery_retain(owner);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return;
retain:
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 (void)wr_iot_mbss_recovery_retain(owner);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
#else
 (void)work;
#endif
}
