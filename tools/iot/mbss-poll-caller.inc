/* Staged binding: adapter must embed wr_iot_mbss_poll_state and
 * wr_iot_mbss_poll_work, initialize both before publication, and include
 * unjoined caller state in every free guard. No ordinary admission yet. */
INT wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad)
{
 ULONG flags;int accepted=0;
 if(!ad)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(wr_iot_mbss_poll_reserve(&ad->wr_iot_mbss_poll_state)){
  accepted=schedule_delayed_work(&ad->wr_iot_mbss_poll_work,HZ/10+1);
  (void)wr_iot_mbss_poll_queue_result(&ad->wr_iot_mbss_poll_state,accepted);
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return accepted?0:-1;
}
VOID wr_iot_mbss_poll_work_fn(struct work_struct *work)
{
 RTMP_ADAPTER *ad;
 ULONG flags;int execute,result=-1,accepted;
 if(!work)return;
 ad=container_of(to_delayed_work(work),RTMP_ADAPTER,wr_iot_mbss_poll_work);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 execute=wr_iot_mbss_poll_begin(&ad->wr_iot_mbss_poll_state);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(execute)result=wr_iot_mbss_recovery_poll(ad);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(execute&&result!=0&&wr_iot_mbss_poll_rearm(&ad->wr_iot_mbss_poll_state)){
  accepted=schedule_delayed_work(&ad->wr_iot_mbss_poll_work,HZ/10+1);
  (void)wr_iot_mbss_poll_queue_result(&ad->wr_iot_mbss_poll_state,accepted);
 }
 wr_iot_mbss_poll_returned(&ad->wr_iot_mbss_poll_state);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
}
/* External teardown only: never invoke from this callback, under RTNL or
 * with driver locks. Stop publication precedes synchronous cancellation. */
INT wr_iot_mbss_poll_join(RTMP_ADAPTER *ad)
{
 ULONG flags;int entered,joined,idle=0,left;
 if(!ad||wr_iot_os_join_context())return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 entered=wr_iot_mbss_poll_join_enter(&ad->wr_iot_mbss_poll_state);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!entered)return -1;
 cancel_delayed_work_sync(&ad->wr_iot_mbss_poll_work);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 joined=wr_iot_mbss_poll_joined(&ad->wr_iot_mbss_poll_state,1);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(joined)idle=wr_iot_mbss_recovery_join_completed(ad)==0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 left=wr_iot_mbss_poll_join_leave(&ad->wr_iot_mbss_poll_state,idle);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return joined&&idle&&left?0:-1;
}
INT wr_iot_mbss_poll_stop_join(RTMP_ADAPTER *ad)
{
 ULONG flags;int joined;
 if(!ad||wr_iot_os_join_context())return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 wr_iot_mbss_poll_stop(&ad->wr_iot_mbss_poll_state);
 wr_iot_mbss_reaper_stop(&ad->wr_iot_mbss_reaper_gate);
 joined=wr_iot_mbss_poll_join_enter(&ad->wr_iot_mbss_poll_state);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!joined)return -1;
 cancel_delayed_work_sync(&ad->wr_iot_mbss_poll_work);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 joined=wr_iot_mbss_poll_joined(&ad->wr_iot_mbss_poll_state,1);
 if(!wr_iot_mbss_poll_join_leave(&ad->wr_iot_mbss_poll_state,0))joined=0;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return joined?0:-1;
}
