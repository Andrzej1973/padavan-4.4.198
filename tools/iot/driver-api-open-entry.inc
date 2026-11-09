/* New Linux-only entry, intentionally uninstalled until owner/open binding is
 * complete. Called from ndo_do_ioctl under RTNL, outside control admission:
 * that admission would conflict with the single BSS_OPEN ticket. Strong
 * request_enter/leave implementations are required; no permissive fallback.
 * Success requires netdev-open and a correlated host TX publication;
 * neither proves RF delivery or network acceptance.
 * No response buffer/key export, firmware command or ACK change. */
static INT wr_iot_driver_open_ioctl(RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq)
{
 struct wr_iot_driver_open_request request={0};
 unsigned char wire[WR_IOT_DRIVER_OPEN_BYTES]={0};
 volatile unsigned char *wipe=wire;
 unsigned int i;int status=-EINVAL,entered=0;
 if(!ad||!dev||!rq)goto done;
 if(!rtnl_is_locked()){status=-EBUSY;goto done;}
 if(!ns_capable(dev_net(dev)->user_ns,CAP_NET_ADMIN)){
  status=-EPERM;goto done;
 }
 if(!IS_MT7603(ad)){status=-EOPNOTSUPP;goto done;}
 if(netif_running(dev)){status=-EBUSY;goto done;}
 if(copy_from_user(wire,rq->ifr_data,sizeof(wire))){status=-EFAULT;goto done;}
 if(!wr_iot_driver_open_decode(&request,wire,sizeof(wire)))goto done;
 /* enter validates exact third-netdev identity, epoch/generation and an idle
  * control/config owner. MBSS open must consume this same task-owned request
  * under its BSS_OPEN ticket and compare loaded credentials before mutation. */
 status=wr_iot_driver_request_enter(ad,dev,&request,current);
 if(status)goto done;
 entered=1;
 status=dev_open(dev);
 if(!status)status=wr_iot_driver_first_beacon_wait(ad,dev,3000);
done:
 if(entered&&!wr_iot_driver_request_leave(ad,dev,current))status=-EUCLEAN;
 wr_iot_driver_request_wipe(&request);
 for(i=0;i<sizeof(wire);i++)wipe[i]=0;
 return status;
}
