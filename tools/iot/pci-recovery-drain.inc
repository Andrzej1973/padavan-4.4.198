/* Isolated PCI retirement candidate. This can complete already-owned
 * recovery before the stop request. A stalled owner still prevents release;
 * no finalizer or physical-unplug recovery is implemented here. */
#define WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS 3U

static int wr_iot_pci_recovery_drain(PRTMP_ADAPTER adapter)
{
 enum wr_iot_pci_drain_decision decision;
 ULONG flags;
 unsigned int round;
 int next_pending, completed;

 for (round = 0; round <= WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS; round++) {
  /* The adapter lock is not held while joining callbacks. The delayed
   * callback may rearm itself; one flush is not a full drain. */
  flush_delayed_work(&adapter->wr_iot_main_recovery_reap_work);
  flush_work(&adapter->wr_iot_main_recovery_work);
  wr_iot_main_recovery_join_complete(adapter);
  next_pending = delayed_work_pending(
    &adapter->wr_iot_main_recovery_reap_work) ||
    work_busy(&adapter->wr_iot_main_recovery_reap_work.work);
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);
  completed = 0;
  decision = wr_iot_pci_retirement_drain_next(
    &adapter->wr_iot_pci_retirement,
    adapter->wr_iot_main_recovery.deferred_owners, 1, next_pending,
    round, WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS);
  if (decision == WR_PCI_DRAIN_COMPLETE)
   completed = wr_iot_pci_retirement_drain_complete(
     &adapter->wr_iot_pci_retirement, 1, 0);
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
  if (decision == WR_PCI_DRAIN_COMPLETE) return completed;
  if (decision == WR_PCI_DRAIN_STALLED) return 0;
 }
 return 0;
}
