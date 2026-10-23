/* Candidate attach bridge. Caller pins adapter/device and serializes attach
 * vs unregister. Registry exists before kernel publication. No lock over RTNL. */
INT wr_iot_netdev_attach_checked(RTMP_ADAPTER *pAd, UCHAR mode,
 PNET_DEV dev, RTMP_OS_NETDEV_OP_HOOK *hook)
{
 struct wr_iot_interface_ref *record;
 unsigned long generation;
 ULONG flags;
 INT status;
 if(!pAd||!dev||!hook)return NDIS_STATUS_FAILURE;
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
 if(pAd->wr_iot_transition.retiring){
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
  return NDIS_STATUS_FAILURE;
 }
 record=wr_iot_registry_add(pAd->wr_iot_interface_refs,WDEV_NUM_MAX+1,
                           &pAd->wr_iot_registration_generation,dev);
 generation=record?record->generation:0;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 if(!record)return NDIS_STATUS_FAILURE;
 status=RtmpOSNetDevAttach(mode,dev,hook);
 if(status!=NDIS_STATUS_SUCCESS){
  /* Failed register did not publish an administratively opened interface.
   * Caller owns failed construction and must still free vendor allocations. */
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
  wr_iot_registry_release(record,dev,generation);
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 }
 if(status==NDIS_STATUS_SUCCESS){
  RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock,flags);
  record->published=1;
  RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock,flags);
 }
 return status;
}
