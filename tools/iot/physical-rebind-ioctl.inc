/* Linux-only bounded wrapper. No route installed by this fragment. Existing
 * CLOSED_CONFIG discriminator must call it only in isolated no-host candidate.
 * The wrapper independently authorizes and copies; userspace races cannot
 * select a different operation/length after the bounded header read. */
#include "physical-rebind-wire.h"
static INT __attribute__((unused)) wr_iot_physical_rebind_ioctl(
 RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq)
{
 unsigned char header[8]={0},wire[WR_REBIND_OPEN_BYTES]={0};
 struct wr_iot_physical_rebind_request request={0};
 volatile unsigned char *wipe=wire;unsigned length=0,i;int status=-EINVAL;
 if(!ad||!dev||!rq)goto done;
 if(!rtnl_is_locked()){status=-EBUSY;goto done;}
 if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN)){status=-EPERM;goto done;}
 if(!IS_MT7603(ad)){status=-EOPNOTSUPP;goto done;}
 if(ad->ApCfg.BssidNum!=3||dev==ad->net_dev||
    ad->ApCfg.MBSSID[2].wdev.if_dev!=dev){status=-EOPNOTSUPP;goto done;}
 if(copy_from_user(header,rq->ifr_data,sizeof(header))){status=-EFAULT;goto done;}
 if(header[0]!='W'||header[1]!='R'||header[2]!='R'||header[3]!='B'||
    header[4]!=1||header[6]||header[7])goto done;
 if(header[5]==WR_REBIND_OBSERVE)length=WR_REBIND_OBSERVE_BYTES;
 else if(header[5]==WR_REBIND_OPEN)length=WR_REBIND_OPEN_BYTES;
 else goto done;
 if(copy_from_user(wire,rq->ifr_data,length)){status=-EFAULT;goto done;}
 for(i=0;i<sizeof(header);i++)if(wire[i]!=header[i])goto done;
 if(!wr_iot_physical_rebind_decode(&request,wire,length))goto done;
 if(request.operation==WR_REBIND_OBSERVE)
  status=wr_iot_physical_rebind_observe(ad,dev,&request.physical);
 else status=wr_iot_physical_rebind_open_execute(ad,dev,&request.physical,&request.open);
 done:
 wr_iot_physical_rebind_wipe(&request);
 for(i=0;i<sizeof(wire);i++)wipe[i]=0;
 return status;
}
