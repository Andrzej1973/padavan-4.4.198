/* Standalone Linux ioctl transport, uninstalled. A strong transaction handler
 * is required; no fallback or default-success implementation is supplied.
 * Outer caller pins netdev/adapter/module for this ioctl and owns RTNL. */
#include "physical-stop-response.h"
INT wr_iot_physical_stop_handle(RTMP_ADAPTER *,PNET_DEV,
 const struct wr_iot_physical_stop_request *,unsigned char *,unsigned int);
static INT __attribute__((unused)) wr_iot_physical_stop_ioctl(RTMP_ADAPTER *ad,
 PNET_DEV dev,struct ifreq *rq)
{
 unsigned char wire[64]={0};struct wr_iot_physical_stop_request request;
 struct wr_iot_physical_stop_response response;ULONG flags=0;int exact,status;
 if(!ad||!dev||!rq)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN))return -EPERM;
 if(!IS_MT7603(ad))return -EOPNOTSUPP;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 exact=ad->net_dev==dev&&ad->ApCfg.BssidNum==3&&
       ad->ApCfg.BssidNum<=sizeof(ad->ApCfg.MBSSID)/sizeof(ad->ApCfg.MBSSID[0])&&
       ad->ApCfg.MBSSID[2].wdev.if_dev&&ad->ApCfg.MBSSID[2].wdev.if_dev!=dev;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EBUSY;
 if(copy_from_user(wire,rq->ifr_data,sizeof(wire)))return -EFAULT;
 if(!wr_iot_physical_stop_request_decode(&request,wire,sizeof(wire)))return -EINVAL;
 /* Handler validates fresh registry/identity and retains all uncertain
  * transactions. No locks held over user copy or resource-return operations. */
 status=wr_iot_physical_stop_handle(ad,dev,&request,wire,sizeof(wire));
 if(status)return status<0?status:-EIO;
 if(!wr_iot_physical_stop_response_decode(&response,wire,sizeof(wire),&request))return -EIO;
 /* Failure here never repeats/cancels a potentially completed operation.
  * Same identity must recover via handler's retained terminal/record state. */
 return copy_to_user(rq->ifr_data,wire,sizeof(wire))?-EFAULT:0;
}
