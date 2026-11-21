/* Staged strong finish; ioctl/RTNL pins adapter until return. Extra holds and
 * active adapter fence survive BOTH outcomes. A separate proven retirement
 * path must own their release; this function never retries or removes isolation. */
static INT wr_iot_driver_close_request_finish(RTMP_ADAPTER *ad,PNET_DEV dev,
 const void *task,int linux_status)
{
 ULONG flags=0;int completed;
 if(!ad||!dev||!task||task!=current)return 0;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 /* Missing holds are an uncertain outcome, never reference-close success.
  * Let the same-owner finish clear its borrowed task even in this case. */
 if(!ad->wr_iot_close_owner.netdev_held||!ad->wr_iot_close_owner.module_held)
  linux_status=-EUCLEAN;
 completed=wr_iot_driver_close_finish_reference(&ad->wr_iot_close_owner,task,dev,
  &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
  ad->net_dev,VIRTUAL_IF_NUM(ad),linux_status);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return completed;
}
