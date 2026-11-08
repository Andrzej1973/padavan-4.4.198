/* Read-only CONFIGURATION result tied to the original successful OPEN nonce.
 * Caller kernel ioctl path holds RTNL/lifetimes; persistent probe context must
 * survive EUCLEAN. No RF/FIFO/late-callback or isolation-release permission. */
static INT wr_iot_driver_closed_ioctl(RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq)
{
 unsigned char wire[WR_IOT_DRIVER_CLOSED_BYTES]={0},nonce[16];
 struct wr_iot_interface_ref *record;
 unsigned long epoch=0,generation=0,token=0,serial=0;ULONG flags=0;
 int matched=0,status;
 if(!ad||!dev||!rq)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;
 if(!wr_iot_driver_closed_query_decode(nonce,wire,sizeof(wire)))return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->wr_iot_closed_probe.active){RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -EUCLEAN;}
 epoch=ad->wr_iot_driver_owner.receipt.epoch;
 generation=ad->wr_iot_driver_owner.receipt.generation;
 token=ad->wr_iot_driver_owner.receipt.open_token;
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation);
 if(record&&wr_iot_driver_open_receipt_matches(&ad->wr_iot_driver_owner,nonce,
    dev,epoch,generation,token)&&ad->wr_iot_transition.epoch==epoch){
  serial=record->close_serial;matched=1;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EAGAIN;
 status=wr_iot_mt7603_closed_probe(ad,dev,&ad->wr_iot_closed_probe,generation,token,serial);
 if(status)return status;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 matched=ad->wr_iot_transition.epoch==epoch&&!ad->wr_iot_control_users&&
  !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
  wr_iot_driver_open_receipt_matches(&ad->wr_iot_driver_owner,nonce,dev,epoch,generation,token)&&
  wr_iot_mbss_closed_reference(&ad->wr_iot_transition,ad->wr_iot_interface_refs,
   WDEV_NUM_MAX+1,ad->net_dev,dev,generation,token,serial,VIRTUAL_IF_NUM(ad));
 if(matched)matched=wr_iot_driver_closed_encode(wire,sizeof(wire),nonce,epoch,generation,token,serial);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EAGAIN;
 return copy_to_user(rq->ifr_data,wire,sizeof(wire))?-EFAULT:0;
}
