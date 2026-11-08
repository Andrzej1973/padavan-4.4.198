/* Proposed synchronous Linux CLOSE entry. Common ioctl has already checked
 * RTNL, CAP_NET_ADMIN, MT7603 and copied the fixed 64-byte request. Strong
 * enter/finish bindings must retain adapter/netdev and recovery ownership.
 * No generic success fallback. A successful result is checked reference
 * closure only; never RF/isolation acceptance. Do not automatically retry. */
static INT wr_iot_driver_close_reply(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct ifreq *rq,unsigned char *wire)
{
 struct wr_iot_driver_close_request request;
 int status;
 (void)rq;
 if(!wr_iot_driver_close_request_decode(&request,wire,64))return -EINVAL;
 if(!netif_running(dev))return -EAGAIN;
 /* Atomically match nonce/epoch/generation/token and reserve one close ticket
  * under the adapter lock; MBSS ndo_stop consumes that exact task-owned ticket. */
 status=wr_iot_driver_close_request_enter(ad,dev,&request,current);
 if(status)return status;
 status=dev_close(dev);
 /* Linux ignores ndo_stop errors. Finish must validate the actual executor's
  * ticket/record completion; admin DOWN and dev_close==0 are insufficient.
  * On any ambiguity retain close provenance and isolation for recovery. */
 if(!wr_iot_driver_close_request_finish(ad,dev,current,status))return -EUCLEAN;
 return status;
}
