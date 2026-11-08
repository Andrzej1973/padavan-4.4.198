/* Staged fixed-body entry gate, not a thread function or module handoff.
 * API owner pins adapter/module before entry. Caller must handle any refusal
 * without dropping that pin or leaving a dead borrowed task pointer behind. */
static INT wr_iot_driver_close_retirement_thread_enter(RTMP_ADAPTER *ad)
{
 ULONG flags=0;int accepted;
 if(!ad||!(current->flags&PF_KTHREAD)||(current->flags&PF_WQ_WORKER))return -EPERM;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 accepted=ad->wr_iot_close_owner.retirement_task==current&&
  ad->wr_iot_close_owner.retirement_started&&!ad->wr_iot_close_owner.retirement_canceling&&
  !ad->wr_iot_close_owner.retirement_entered&&
  wr_iot_driver_close_retirement_ready_locked(ad);
 if(accepted)ad->wr_iot_close_owner.retirement_entered=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return accepted?0:-EBUSY;
}

/* Matching designated task, before returning to core after failed validation.
 * API keeps its module reference and adapter fence, so returning module text
 * remains live. Clear only this task's borrowed pointer; no ref/drop or retry.
 * A concurrent cancellation fence stays set for its external stop owner. */
static INT wr_iot_driver_close_retirement_thread_refuse(RTMP_ADAPTER *ad,int error)
{
 ULONG flags=0;int matched;
 if(!ad||error>=0)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=ad->wr_iot_close_owner.active&&ad->wr_iot_close_owner.module_held&&
         ad->wr_iot_close_owner.retirement_task==current;
 if(matched){
  ad->wr_iot_close_owner.retirement_task=NULL;
  ad->wr_iot_close_owner.retirement_started=0;
  ad->wr_iot_close_owner.retirement_entered=0;
  ad->wr_iot_close_owner.retirement_error=error;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return matched;
}
