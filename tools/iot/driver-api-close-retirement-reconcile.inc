/* Nonwaiting return of the tracked caller task reference after fixed-body
 * refusal. Caller owns RTNL, adapter/registration and this handle exclusively.
 * Pinned 4.4 kthread bootstrap publishes vfork_done before create returns;
 * core mm_release clears it and completes exit under task_lock. Observing NULL
 * under that same lock proves return to core, not complete task deallocation.
 * No kthread_stop, module put, RF receipt or OPEN permission is issued here. */
static INT wr_iot_driver_close_retirement_reconcile(RTMP_ADAPTER *ad,
 struct task_struct **handle)
{
 struct task_struct *task;ULONG flags=0;
 const void *device;unsigned long generation,token,epoch,serial;int exited,matched;
 if(!ad||!handle||!*handle)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 task=*handle;if(task==current)return -EDEADLK;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=ad->wr_iot_close_owner.active&&ad->wr_iot_close_owner.module_held&&
  ad->wr_iot_close_owner.retirement_handle==task&&
  !ad->wr_iot_close_owner.retirement_task&&!ad->wr_iot_close_owner.task&&
  !ad->wr_iot_close_owner.retirement_started&&!ad->wr_iot_close_owner.retirement_entered&&
  !ad->wr_iot_close_owner.retirement_canceling&&!ad->wr_iot_close_owner.retirement_module_transferred&&
  ad->wr_iot_close_owner.retirement_error<0;
 if(!matched){RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -EBUSY;}
 device=ad->wr_iot_close_owner.device;generation=ad->wr_iot_close_owner.generation;
 token=ad->wr_iot_close_owner.open_token;epoch=ad->wr_iot_close_owner.ticket.epoch;
 serial=ad->wr_iot_close_owner.ticket.serial;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 /* Never nest adapter transition lock with the task's alloc_lock. */
 task_lock(task);exited=task->vfork_done==NULL;task_unlock(task);
 if(!exited)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=ad->wr_iot_close_owner.active&&ad->wr_iot_close_owner.module_held&&
  ad->wr_iot_close_owner.retirement_handle==task&&
  !ad->wr_iot_close_owner.retirement_task&&!ad->wr_iot_close_owner.task&&
  !ad->wr_iot_close_owner.retirement_started&&!ad->wr_iot_close_owner.retirement_entered&&
  !ad->wr_iot_close_owner.retirement_canceling&&!ad->wr_iot_close_owner.retirement_module_transferred&&
  ad->wr_iot_close_owner.retirement_error<0&&
  ad->wr_iot_close_owner.device==device&&ad->wr_iot_close_owner.generation==generation&&
  ad->wr_iot_close_owner.open_token==token&&ad->wr_iot_close_owner.ticket.epoch==epoch&&
  ad->wr_iot_close_owner.ticket.serial==serial;
 if(matched)ad->wr_iot_close_owner.retirement_handle=NULL;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EUCLEAN;
 put_task_struct(task);*handle=NULL;return 0;
}
