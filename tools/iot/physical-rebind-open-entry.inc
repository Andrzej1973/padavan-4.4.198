/* Internal execution only: outer transport must capability-check and decode
 * both bounded requests first, while retaining RTNL/adapter/netdevice lifetime.
 * Uses the existing actual ndo_open, loaded-key and first-beacon pipeline.
 * No retry, alternate firmware command, caller-config mutation or new ioctl. */
static INT __attribute__((unused)) wr_iot_physical_rebind_open_execute(
 RTMP_ADAPTER *ad,PNET_DEV dev,const struct wr_iot_physical_stop_request *physical,
 const struct wr_iot_driver_open_request *input)
{
 struct wr_iot_driver_open_request request={0};int status=-EINVAL,entered=0;
 if(!ad||!dev||!physical||!input)return -EINVAL;
 request=*input;
 if(!rtnl_is_locked()){status=-EBUSY;goto done;}
 if(!IS_MT7603(ad)){status=-EOPNOTSUPP;goto done;}
 if(netif_running(dev)){status=-EBUSY;goto done;}
 status=wr_iot_physical_rebind_request_enter(ad,dev,physical,&request);
 if(status)goto done;
 entered=1;
 status=dev_open(dev);
 if(!status)status=wr_iot_driver_first_beacon_wait(ad,dev,3000);
 done:
 if(entered&&!wr_iot_driver_request_leave(ad,dev,current))status=-EUCLEAN;
 wr_iot_driver_request_wipe(&request);
 return status;
}
