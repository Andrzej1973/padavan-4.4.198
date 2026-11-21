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