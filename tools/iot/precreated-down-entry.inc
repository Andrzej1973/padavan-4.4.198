/* Unrouted fixed ra2 observation. Kernel private ioctl holds RTNL; caller
 * verifies adapter allocation lifetime through its unregister/free contract.
 * No permission to stop/reopen or release DMA/IRQ follows this response. */
#include "precreated-down-wire.h"
static INT __attribute__((unused)) wr_iot_precreated_down_ioctl(
 PRTMP_ADAPTER ad,PNET_DEV dev,struct ifreq *rq)
{
 unsigned char wire[64];int status;
 if(!ad||!dev||!rq)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 if(!READ_ONCE(ad->wr_iot_recovery_storage_live)||ad->ApCfg.BssidNum!=3||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=dev||dev==ad->net_dev)return -EAGAIN;
 if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;
 status=wr_iot_precreated_down_reply(ad,dev,wire,sizeof(wire),wire);
 if(status)return status;
 return copy_to_user(rq->ifr_data,wire,sizeof(wire))?-EFAULT:0;
}
