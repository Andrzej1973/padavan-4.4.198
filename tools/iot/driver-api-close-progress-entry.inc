/* Proposed progress reply. Common ioctl must enforce RTNL, CAP_NET_ADMIN,
 * MT7603 and fixed64 copy first, exactly as CLOSE. Not routed/installed yet.
 * No netif_running precondition: this advances existing CLOSE after admin DOWN.
 * Never opens/closes a netdev or treats reference status as RF acceptance. */
static INT wr_iot_driver_close_progress_reply(RTMP_ADAPTER *ad,PNET_DEV dev,
 const unsigned char *wire)
{
 struct wr_iot_driver_close_request request;
 if(!wr_iot_driver_close_progress_decode(&request,wire,64))return -EINVAL;
 return wr_iot_driver_close_progress(ad,dev,&request);
}
