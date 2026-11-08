/* Staged standalone transport for operation13, not installed in netdev ops.
 * Fixed64 copy has no user length field (struct ifreq private transport).
 * Decoder enforces exact internal format. No callback fallback or RF claim. */
static INT wr_iot_driver_close_progress_ioctl(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq)
{
 unsigned char wire[64]={0};ULONG flags=0;int exact;
 if(!ad||!dev||!rq)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 exact=ad->ApCfg.BssidNum==3&&ad->net_dev!=dev&&
  ad->ApCfg.MBSSID[2].wdev.if_dev==dev;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EBUSY;
 if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;
 return wr_iot_driver_close_progress_reply(ad,dev,wire);
}
