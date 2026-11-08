/* Nonsecret CLOSED-BSS identity observation, called under ioctl RTNL.
 * Does not reserve an open or promise that this identity remains current. */
static INT wr_iot_driver_identity_ioctl(RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq)
{
 unsigned char wire[WR_IOT_DRIVER_IDENTITY_BYTES]={0};
 struct wr_iot_interface_ref *record,*main_ref;
 ULONG flags=0;int ready=0;
 if(!ad||!dev||!rq)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 record=wr_iot_registry_find_openable(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev);
 main_ref=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev);
 if(ad->ApCfg.BssidNum>=3&&ad->ApCfg.BssidNum<=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0])&&
    ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&dev!=ad->net_dev&&!netif_running(dev)&&
    record&&record->family==WR_REF_FAMILY_MBSS&&main_ref&&main_ref->family==WR_REF_FAMILY_MAIN&&
    !main_ref->removing&&VIRTUAL_IF_NUM(ad)&&
    wr_iot_registry_count_matches(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad))&&
    !ad->wr_iot_driver_owner.active&&!ad->wr_iot_driver_owner.poisoned&&
    !ad->wr_iot_control_users&&!ad->wr_iot_control_poisoned&&
    !ad->wr_iot_boot_active&&!ad->wr_iot_boot_failed&&
    ad->wr_iot_transition.phase==WR_RADIO_READY&&ad->wr_iot_transition.main_ready&&
    !ad->wr_iot_transition.busy&&!ad->wr_iot_transition.main_inhibited&&
    !ad->wr_iot_transition.reset_pending&&!ad->wr_iot_transition.retiring&&
    !ad->wr_iot_transition.pm_suspending&&!ad->wr_iot_transition.pm_suspended)
  ready=wr_iot_driver_identity_encode(wire,sizeof(wire),ad->wr_iot_transition.epoch,record->generation);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!ready)return -EBUSY;
 return copy_to_user(rq->ifr_data,wire,sizeof(wire))?-EFAULT:0;
}
