/* Called before legacy begin_close reserves a ticket. Return 0 for an owned
 * handoff, 1 only when no CLOSE API owner exists, -1 on owned-path refusal.
 * A failed owned transfer must never fall through to a second begin_stop.
 * Caller pins adapter/netdev; this operation does not sleep or touch hardware. */
static INT wr_iot_driver_close_take_bound(RTMP_ADAPTER *ad,PNET_DEV dev,
 struct wr_iot_radio_ticket *ticket,unsigned long *generation)
{
 ULONG flags=0;int result=1;
 if(!ad||!dev||!ticket||!generation)return -1;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(ad->wr_iot_close_owner.active){
  result=-1;
  if(IS_MT7603(ad)&&ad->ApCfg.BssidNum==3&&
     ad->ApCfg.MBSSID[2].wdev.if_dev==dev&&ad->net_dev!=dev&&
     wr_iot_driver_close_take(&ad->wr_iot_close_owner,current,dev,
       &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
       ticket,generation))result=0;
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return result;
}
