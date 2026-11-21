/* Recovery CLOSE token only; never a successful first-publication reply. */
/* Called after existing CLOSED ioctl RTNL/capability/user-copy checks. Only
 * exact reserved ra2 is accepted, and snapshot never touches hardware. */
static INT wr_iot_driver_open_recovery_reply(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq,unsigned char *wire)
{
 unsigned char nonce[16];ULONG flags=0;int matched=0;
 struct wr_iot_driver_open_current_result observed;
 if(!wr_iot_driver_open_recovery_query_decode(nonce,wire,64))return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->ApCfg.BssidNum==3&&ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&
    !ad->wr_iot_close_owner.active)
  matched=wr_iot_driver_open_recovery_observe(&ad->wr_iot_driver_owner,nonce,
    &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
    ad->net_dev,dev,VIRTUAL_IF_NUM(ad),ad->wr_iot_control_users,
    ad->wr_iot_control_poisoned||ad->wr_iot_boot_active||ad->wr_iot_boot_failed,
    ad->wr_iot_closed_probe.active,&observed);
 if(matched)matched=wr_iot_driver_open_recovery_encode(wire,64,nonce,
    observed.adapter_epoch,observed.device_generation,observed.open_token);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EAGAIN;
 return copy_to_user(rq->ifr_data,wire,64)?-EFAULT:0;
}
