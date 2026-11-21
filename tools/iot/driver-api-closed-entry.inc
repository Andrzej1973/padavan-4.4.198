/* Read-only original uncertain OPEN provenance. RTNL/capability checked by
 * common entry; no hardware access, poison clear, or acceptance permission. */
static INT wr_iot_driver_uncertain_reply(RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq,unsigned char *wire)
{
 unsigned char nonce[16];ULONG flags=0;unsigned int i,difference=0;int matched=0;
 struct wr_iot_driver_owner *owner=&ad->wr_iot_driver_owner;
 struct wr_iot_interface_ref *record;
 if(!wr_iot_driver_uncertain_query_decode(nonce,wire,WR_IOT_DRIVER_CLOSED_BYTES))return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,owner->claim.generation);
 for(i=0;i<16;i++)difference|=nonce[i]^owner->uncertain_request_id[i];
 if(!difference&&owner->poisoned&&!owner->active&&owner->claim.device==dev&&
    owner->claim.operation==WR_RADIO_BSS_OPEN&&record&&record->published&&!record->removing&&
    record->family==WR_REF_FAMILY_MBSS&&record->last_token==owner->claim.serial&&
    owner->claim.epoch==ad->wr_iot_transition.epoch)
  matched=wr_iot_driver_uncertain_encode(wire,WR_IOT_DRIVER_CLOSED_BYTES,nonce,
   owner->claim.epoch,owner->claim.generation,owner->claim.serial);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EAGAIN;
 return copy_to_user(rq->ifr_data,wire,WR_IOT_DRIVER_CLOSED_BYTES)?-EFAULT:0;
}
/* Called only after the common RTNL/capability/copy checks below. Returns
 * historical no-mutation provenance, never CLOSED/RF or rollback permission. */
static INT wr_iot_driver_refusal_reply(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq,unsigned char *wire)
{
 unsigned char nonce[16];ULONG flags=0;int matched=0;
 struct wr_iot_interface_ref *record,*main_ref;
 unsigned long epoch,generation,token;
 if(!wr_iot_driver_refusal_query_decode(nonce,wire,WR_IOT_DRIVER_CLOSED_BYTES))return -EINVAL;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 epoch=ad->wr_iot_driver_owner.refusal.epoch;
 generation=ad->wr_iot_driver_owner.refusal.generation;
 token=ad->wr_iot_driver_owner.refusal.open_token;
 record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation);
 main_ref=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev);
 if(!ad->wr_iot_closed_probe.active&&!ad->wr_iot_control_users&&
    !ad->wr_iot_control_poisoned&&!ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
    record&&record->phase==WR_REF_IDLE&&record->open_unmutated&&record->published&&
    record->family==WR_REF_FAMILY_MBSS&&!record->removing&&record->last_token==token&&
    main_ref&&main_ref->family==WR_REF_FAMILY_MAIN&&!main_ref->removing&&
    wr_iot_registry_count_matches(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad))&&
    ad->wr_iot_transition.epoch==epoch&&ad->wr_iot_transition.phase==WR_RADIO_READY&&
    ad->wr_iot_transition.main_ready&&!ad->wr_iot_transition.main_inhibited&&
    !ad->wr_iot_transition.busy&&!ad->wr_iot_transition.reset_pending&&
    !ad->wr_iot_transition.retiring&&!ad->wr_iot_transition.exhausted&&!ad->wr_iot_transition.pm_suspending&&
    !ad->wr_iot_transition.pm_suspended&&
    wr_iot_driver_refusal_matches(&ad->wr_iot_driver_owner,nonce,dev,epoch,generation,token))
  matched=wr_iot_driver_refusal_encode(wire,WR_IOT_DRIVER_CLOSED_BYTES,nonce,epoch,generation,token);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!matched)return -EAGAIN;
 return copy_to_user(rq->ifr_data,wire,WR_IOT_DRIVER_CLOSED_BYTES)?-EFAULT:0;
}
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
 if(wire[4]==8)return wr_iot_driver_uncertain_reply(ad,dev,rq,wire);
 if(wire[4]==6)return wr_iot_driver_refusal_reply(ad,dev,rq,wire);
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
