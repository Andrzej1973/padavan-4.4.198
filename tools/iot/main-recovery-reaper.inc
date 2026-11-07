/* Staged only: a joined external reaper owns the netdev hold and retry.
 * The unresolved PCI incomplete-owner path keeps this out of production. */
#define WR_IOT_MAIN_RECOVERY_MAX_ATTEMPTS 3U

INT wr_iot_main_recovery_join_complete(RTMP_ADAPTER *adapter)
{
 struct wr_iot_main_recovery_owner *owner;
 const void *device = NULL;
 ULONG flags;
 int completed = 0;
 if (!adapter) return 0;
 owner = &adapter->wr_iot_main_recovery;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 if (owner->completed && owner->module_pin_released) {
  device = owner->device;
  completed = wr_iot_main_recovery_complete(owner, 1);
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (completed)
  dev_put((struct net_device *)device);
 return completed;
}

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

static int wr_iot_main_verify_recovery_submit(PRTMP_ADAPTER adapter,
 struct net_device *net_dev,unsigned long generation,
 const struct wr_iot_radio_ticket *close_ticket)
{
 struct wr_iot_interface_ref *record;
 struct wr_iot_main_recovery_owner *owner;
 ULONG flags;
 int queued = 0, accepted, reaper_accepted = 0;
 if (!adapter || !net_dev || !generation) return 0;
 /* ndo_open owns RTNL here. The adapter lock serializes this acquisition
  * with PCI retirement; deferred_owners then fences adapter release. */
 dev_hold(net_dev);
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
 owner = &adapter->wr_iot_main_recovery;
 record = wr_iot_registry_find(adapter->wr_iot_interface_refs,
                               WDEV_NUM_MAX + 1, net_dev, generation);
 if (record && record->phase == WR_REF_CLOSING && close_ticket)
  queued = wr_iot_main_recovery_queue_close(owner,
    &adapter->wr_iot_transition, record, adapter->wr_iot_interface_refs,
    WDEV_NUM_MAX + 1, close_ticket, VIRTUAL_IF_NUM(adapter),
    1, 1, WR_MAIN_QUEUE_NORMAL, 0);
 else if (record && record->phase == WR_REF_OWNED)
  queued = wr_iot_main_recovery_queue(owner,
    &adapter->wr_iot_transition, record, WR_MAIN_RECOVERY_OPEN_ACQUIRED,
    1, 1, WR_MAIN_QUEUE_NORMAL, 0);
 if (queued) {
  accepted = schedule_work(&adapter->wr_iot_main_recovery_work);
  wr_iot_main_recovery_schedule_result(owner, accepted);
  reaper_accepted = schedule_delayed_work(
    &adapter->wr_iot_main_recovery_reap_work, HZ / 10 + 1);
 }
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
 if (!queued)
  dev_put(net_dev);
 return queued && reaper_accepted;
}
