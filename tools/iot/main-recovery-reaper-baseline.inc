VOID wr_iot_main_recovery_reap_work_fn(struct work_struct *work)
{
 PRTMP_ADAPTER adapter;
 struct wr_iot_main_recovery_owner *owner;
 ULONG flags;
 int reschedule = 0, accepted, pending_canceled, warn_retained = 0;
 if (!work) return;
 adapter = container_of(to_delayed_work(work), RTMP_ADAPTER,
                        wr_iot_main_recovery_reap_work);
 /* This is not the main work item; joining it proves a previous callback
  * has returned before retrying or releasing its netdev hold. */
 pending_canceled = cancel_work_sync(&adapter->wr_iot_main_recovery_work);
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 wr_iot_main_recovery_canceled_before_run(
   &adapter->wr_iot_main_recovery, pending_canceled);
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (wr_iot_main_recovery_join_complete(adapter)) return;
 owner = &adapter->wr_iot_main_recovery;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 if (!owner->stop_requested && owner->phase == WR_MAIN_OWNER_RETAINED &&
     wr_iot_main_recovery_requeue(owner,
       WR_IOT_MAIN_RECOVERY_MAX_ATTEMPTS, 1)) {
  accepted = schedule_work(&adapter->wr_iot_main_recovery_work);
  wr_iot_main_recovery_schedule_result(owner, accepted);
 }
 if (!owner->stop_requested && owner->deferred_owners &&
     (owner->phase == WR_MAIN_OWNER_QUEUED ||
      owner->phase == WR_MAIN_OWNER_RETAINED) &&
     owner->attempts < WR_IOT_MAIN_RECOVERY_MAX_ATTEMPTS &&
     owner->failed_submissions < WR_IOT_MAIN_RECOVERY_MAX_ATTEMPTS -
                                 owner->attempts)
  reschedule = schedule_delayed_work(
    &adapter->wr_iot_main_recovery_reap_work, HZ / 10 + 1);
 warn_retained = !reschedule && owner->deferred_owners &&
                 !owner->stop_requested;
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (warn_retained)
  DBGPRINT(RT_DEBUG_ERROR,
   ("MT7603 main recovery reaper stopped with retained owner\n"));
}