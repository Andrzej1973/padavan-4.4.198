/* Dormant transaction provider. Caller ioctl owns RTNL, capability and outer
 * adapter/module/netdev references. ARM never issues DOWN; QUERY never resubmits
 * a worker. All uncertain cleanup retains adapter-owned state. */
INT wr_iot_physical_stop_handle(RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_physical_stop_request *request,unsigned char *wire,unsigned int length)
{
 struct wr_iot_physical_stop_request query;
 unsigned long serial=0;unsigned long long attempt=0;ULONG flags=0;
 int active,status,i;
 if(!wire||length!=64)return -EINVAL;
 for(i=0;i<64;i++)wire[i]=0;
 if(!ad||!dev||!wr_iot_physical_stop_request_valid(request))return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!IS_MT7603(ad)||ad->net_dev!=dev||ad->ApCfg.BssidNum!=3)return -EOPNOTSUPP;
 if(request->action==WR_STOP_CANCEL||request->action==WR_STOP_RELEASE){
  if(wr_iot_physical_stop_terminal_reply(&ad->wr_iot_physical_terminal,
     request,wire,length))return 0;
 }
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 serial=ad->wr_iot_physical_lifetime.serial;
 active=ad->wr_iot_physical_lifetime.active;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(request->action==WR_STOP_ARM){
  if(active){
   /* Lost ARM reply: observe original record, never acquire another bundle. */
   RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
   attempt=ad->wr_iot_physical_stop.serial;
   RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
   query=*request;query.action=WR_STOP_QUERY;query.attempt=attempt;
   status=wr_iot_physical_stop_query_owned(ad,dev,&query,serial,wire,length);
   if(status)return status;
   if(wire[6]!=WR_STOP_ARMED){for(i=0;i<64;i++)wire[i]=0;return -EALREADY;}
   return wr_iot_physical_stop_response_encode(wire,length,request,attempt,WR_STOP_ARMED)?0:-EIO;
  }
  status=wr_iot_physical_stop_arm_replace_terminal(ad,dev,request,&serial);
  if(status)return status;
  if(!wr_iot_physical_stop_pins_acquire(&ad->wr_iot_physical_pending_pins,
      current,(struct net_device *)dev)){
   status=wr_iot_physical_stop_arm_abort_unpublished(ad,dev,serial);
   return status?status:-ENOMEM;
  }
  status=wr_iot_physical_stop_arm_publish_owned(ad,dev,request,serial,
    &ad->wr_iot_physical_pins,&ad->wr_iot_physical_pending_pins,&attempt);
  if(status){
   if(!wr_iot_physical_stop_pins_drop(&ad->wr_iot_physical_pending_pins))return -EUCLEAN;
   if(wr_iot_physical_stop_arm_abort_unpublished(ad,dev,serial))return -EUCLEAN;
   return status;
  }
  return wr_iot_physical_stop_response_encode(wire,length,request,attempt,WR_STOP_ARMED)?0:-EIO;
 }
 if(!active)return -EAGAIN;
 if(request->action==WR_STOP_QUERY){
  /* Completion only records already-returned checked recovery receipts. */
  status=wr_iot_physical_stop_query_owned(ad,dev,request,serial,wire,length);
  if(status)return status;
  if(wire[6]==WR_STOP_RUNNING)
   (void)wr_iot_physical_stop_main_complete(ad,dev,serial);
  return wr_iot_physical_stop_query_owned(ad,dev,request,serial,wire,length);
 }
 if(request->action==WR_STOP_CANCEL)
  status=wr_iot_physical_stop_cancel_owned(ad,dev,request,serial,&ad->wr_iot_physical_terminal);
 else status=wr_iot_physical_stop_release_owned(ad,dev,request,serial,&ad->wr_iot_physical_terminal);
 if(status)return status;
 return wr_iot_physical_stop_terminal_reply(&ad->wr_iot_physical_terminal,
   request,wire,length)?0:-EUCLEAN;
}
