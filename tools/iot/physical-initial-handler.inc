/* Dormant typed transaction provider. Outer ioctl owns RTNL, capability and
 * independent adapter/Main/module lifetime. ARM never submits physical DOWN. */
static INT __attribute__((unused)) wr_iot_physical_initial_handle(
 RTMP_ADAPTER *ad,PNET_DEV dev,
 const struct wr_iot_physical_initial_request *request,
 unsigned char *wire,unsigned int length)
{
 struct wr_iot_physical_initial_request query,reply;
 unsigned long serial=0;unsigned long long attempt=0;ULONG flags=0;
 int active,status;unsigned i;
 if(!wire||length!=64)return -EINVAL;
 for(i=0;i<length;i++)wire[i]=0;
 if(!ad||!dev||!wr_iot_physical_initial_valid(request,0))return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!IS_MT7603(ad)||ad->net_dev!=dev||ad->ApCfg.BssidNum!=3)return -EOPNOTSUPP;
 if(request->action==WR_STOP_CANCEL||request->action==WR_STOP_RELEASE){
  if(ad->wr_iot_physical_initial_terminal.owner){
   if(!wr_iot_physical_initial_terminal_matches(&ad->wr_iot_physical_initial_terminal,request))return -EBUSY;
  }else{
   /* Validate caller/identity before allocating a persistent terminal cache.
    * A foreign attempt must not occupy the legitimate owner's retry slot. */
   query=*request;query.action=WR_STOP_QUERY;
   status=wr_iot_physical_initial_query_owned(ad,dev,&query,wire,length);
   for(i=0;i<length;i++)wire[i]=0;
   if(status)return status;
  }
  status=wr_iot_physical_initial_cleanup(ad,dev,request,&ad->wr_iot_physical_initial_terminal);
  if(status)return status;
  return wr_iot_physical_initial_terminal_reply(&ad->wr_iot_physical_initial_terminal,
    request,wire,length)?0:-EUCLEAN;
 }
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 active=ad->wr_iot_physical_lifetime.active;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(request->action==WR_STOP_ARM){
  if(active){
   RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
   attempt=ad->wr_iot_physical_initial.serial;
   RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
   query=*request;query.action=WR_STOP_QUERY;query.attempt=attempt;
   status=wr_iot_physical_initial_query_owned(ad,dev,&query,wire,length);
   if(status)return status;
   status=wire[6];for(i=0;i<length;i++)wire[i]=0;
   if(status!=WR_STOP_ARMED)return -EALREADY;
  }else{
   status=wr_iot_physical_initial_arm_replace_terminal(ad,dev,request,&serial);
   if(status)return status;
   if(!wr_iot_physical_stop_pins_acquire(&ad->wr_iot_physical_pending_pins,current,(struct net_device *)dev)){
    status=wr_iot_physical_initial_arm_abort_unpublished(ad,dev,serial);
    return status?status:-ENOMEM;
   }
   status=wr_iot_physical_initial_arm_publish(ad,dev,request,
     &ad->wr_iot_physical_pending_pins,&attempt);
   if(status){
    if(!wr_iot_physical_stop_pins_drop(&ad->wr_iot_physical_pending_pins))return -EUCLEAN;
    if(wr_iot_physical_initial_arm_abort_unpublished(ad,dev,serial))return -EUCLEAN;
    return status;
   }
  }
  reply=*request;reply.attempt=attempt;
  return wr_iot_physical_initial_encode(wire,length,&reply,WR_STOP_ARMED)?0:-EIO;
 }
 if(request->action!=WR_STOP_QUERY||!active)return -EAGAIN;
 status=wr_iot_physical_initial_query_owned(ad,dev,request,wire,length);
 if(status)return status;
 if(wire[6]==WR_STOP_RUNNING){
  (void)wr_iot_physical_initial_main_complete(ad,dev,request->attempt);
  return wr_iot_physical_initial_query_owned(ad,dev,request,wire,length);
 }
 return 0;
}
