/* Caller owns the extra task_struct ref returned by prepare, pins adapter and
 * holds RTNL and serializes wake/stop for this task. Never call from the designated task.
 * Success consumes caller's task ref; any ambiguous outcome retains handle,
 * API module pin and cancellation fence for explicit recovery. */
static INT wr_iot_driver_close_retirement_cancel(RTMP_ADAPTER *ad,
 struct task_struct **handle)
{
 struct task_struct *task;ULONG flags=0;
 unsigned long generation,serial,epoch,token;const void *device;int status,matched;
 if(!ad||!handle||!*handle)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 task=*handle;
 if(task==current)return -EDEADLK;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(!ad->wr_iot_close_owner.active||!ad->wr_iot_close_owner.module_held||
    ad->wr_iot_close_owner.retirement_task!=task||ad->wr_iot_close_owner.retirement_handle!=task||
    ad->wr_iot_close_owner.retirement_started||ad->wr_iot_close_owner.retirement_entered||ad->wr_iot_close_owner.retirement_canceling){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -EBUSY;
 }
 device=ad->wr_iot_close_owner.device;token=ad->wr_iot_close_owner.open_token;
 generation=ad->wr_iot_close_owner.generation;
 serial=ad->wr_iot_close_owner.ticket.serial;epoch=ad->wr_iot_close_owner.ticket.epoch;
 ad->wr_iot_close_owner.retirement_canceling=1;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 status=kthread_stop(task);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=status==-EINTR&&ad->wr_iot_close_owner.active&&ad->wr_iot_close_owner.module_held&&
  ad->wr_iot_close_owner.retirement_task==task&&ad->wr_iot_close_owner.retirement_handle==task&&ad->wr_iot_close_owner.retirement_canceling&&
  !ad->wr_iot_close_owner.retirement_started&&
  ad->wr_iot_close_owner.device==device&&ad->wr_iot_close_owner.open_token==token&&
  ad->wr_iot_close_owner.generation==generation&&
  ad->wr_iot_close_owner.ticket.serial==serial&&ad->wr_iot_close_owner.ticket.epoch==epoch;
 if(matched){ad->wr_iot_close_owner.retirement_handle=NULL;ad->wr_iot_close_owner.retirement_task=NULL;ad->wr_iot_close_owner.retirement_canceling=0;}
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EUCLEAN;
 put_task_struct(task);*handle=NULL;return 0;
}
