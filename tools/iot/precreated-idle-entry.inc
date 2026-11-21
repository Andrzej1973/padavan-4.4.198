/* Experimental common entry has already checked RTNL, CAP_NET_ADMIN,
 * MT7603 and copied64 bytes. Persistent adapter probe storage/lifetime and
 * its teardown fence must be installed before this fragment may be routed. */
static INT wr_iot_precreated_idle_reply(PRTMP_ADAPTER ad,PNET_DEV dev,
 struct ifreq *rq,unsigned char *wire)
{
 unsigned char nonce[16];ULONG flags=0;
 struct wr_iot_interface_ref *record;unsigned long generation=0;int status,matched;
 if(!wr_iot_idle_query_decode(nonce,wire,64))return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find_openable(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev);
 if(record&&record->family==WR_REF_FAMILY_MBSS)generation=record->generation;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!generation)return -EAGAIN;
 status=wr_iot_precreated_idle_probe_driver(ad,dev,&ad->wr_iot_idle_probe,generation);
 if(status)return status;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&!ad->wr_iot_control_users&&
  !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
  !ad->wr_iot_close_owner.active&&
  wr_iot_precreated_idle_probe_current(&ad->wr_iot_idle_probe,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,dev,generation,VIRTUAL_IF_NUM(ad));
 if(matched)matched=wr_iot_idle_reply_encode(wire,64,nonce,
  ad->wr_iot_idle_probe.ticket.epoch,generation,ad->wr_iot_idle_probe.ticket.serial);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EAGAIN;
 return copy_to_user(rq->ifr_data,wire,64)?-EFAULT:0;
}
