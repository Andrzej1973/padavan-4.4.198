/* Staged stopped-task preparation only; never wakes a task or transfers the
 * API module hold. Caller pins adapter and excludes competing retirement
 * preparers throughout. Success returns one extra task_struct ref; caller must
 * preserve it until its eventual wake/stop lifecycle is explicitly completed.
 * The future fixed retirement body must separately claim its module ownership. */
static INT wr_iot_driver_close_retirement_prepare(RTMP_ADAPTER *ad,
 int (*threadfn)(void *),struct task_struct **out)
{
 struct task_struct *task;ULONG flags=0;int ready;
 if(!out)return -EINVAL;
 *out=NULL;
 if(!ad||!threadfn)return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ready=!ad->wr_iot_close_owner.retirement_task&&
       !ad->wr_iot_close_owner.retirement_started&&!ad->wr_iot_close_owner.retirement_entered&&
       !ad->wr_iot_close_owner.retirement_canceling&&
       wr_iot_driver_close_retirement_ready_locked(ad);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return -EBUSY;
 task=kthread_create(threadfn,ad,"wr-iot-retire");
 if(IS_ERR(task))return PTR_ERR(task);
 if(!task)return -EUCLEAN; /* Kernel API promises task or ERR_PTR. */
 get_task_struct(task);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ready=wr_iot_driver_close_retirement_designate_locked(ad,task);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready){
  /* Task was never woken. Core bootstrap skips threadfn on SHOULD_STOP. */
  (void)kthread_stop(task);
  put_task_struct(task);
  return -EBUSY;
 }
 *out=task;return 0;
}
