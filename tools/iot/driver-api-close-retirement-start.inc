/* Staged wake of a prepared dedicated task. Caller owns prepare's task ref,
 * runs in the private ioctl callback under RTNL, pins adapter and serializes
 * start/cancel. Stable Main keeps its original module pin across callback return. Module hold stays API-owned until
 * the future fixed thread body atomically claims it. No resource retirement.
 * Success consumes caller task ref/handle; ambiguous wake keeps both and the
 * started fence, so caller must not treat this as a safely stopped task. */
static INT wr_iot_driver_close_retirement_start(RTMP_ADAPTER *ad,
 struct task_struct **handle)
{
 struct task_struct *task;ULONG flags=0;int woke;
 if(!ad||!handle||!*handle)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 task=*handle;
 if(task==current)return -EDEADLK;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->wr_iot_close_owner.retirement_task!=task||
    ad->wr_iot_close_owner.retirement_started||ad->wr_iot_close_owner.retirement_entered||ad->wr_iot_close_owner.retirement_canceling||
    !wr_iot_driver_close_retirement_ready_locked(ad)){
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -EBUSY;
 }
 ad->wr_iot_close_owner.retirement_started=1;
 woke=wake_up_process(task);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!woke)return -EUCLEAN;
 put_task_struct(task);*handle=NULL;return 0;
}
