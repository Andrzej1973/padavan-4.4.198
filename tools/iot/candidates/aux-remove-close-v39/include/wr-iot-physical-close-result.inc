/* Candidate physical-close result bridge. Sole caller owns current CLOSE ticket
 * and pins adapter/netdevice lifetime through this function and any retry. */
INT wr_iot_rt28xx_close_checked(VOID *dev,
 const struct wr_iot_radio_ticket *ticket)
{
 struct net_device *net_dev = (struct net_device *)dev;
 PRTMP_ADAPTER adapter;
 ULONG flags;
 int notified;
 if (!net_dev || !ticket) return -1;
 adapter = RTMP_OS_NETDEV_GET_PRIV(net_dev);
 if (!adapter) return -1;
 if (wr_iot_drv_close_checked(adapter,net_dev,ticket) != NDIS_STATUS_SUCCESS)
  return -1;
 RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
 notified=adapter->wr_iot_transition.close_notified;
 RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 if (!notified) {
#ifdef WIFI_DIAG
  DiagProcExit(adapter);
#endif
  RTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock,flags);
  adapter->wr_iot_transition.close_notified=1;
  RTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock,flags);
 }
 /* Software close success, not hardware/RF observation or permission to free. */
 return 0;
}
