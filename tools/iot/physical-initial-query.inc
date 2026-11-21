/* Read-only INITIAL_OFF observation. Caller retains adapter/Main lifetime and
 * RTNL. Does not start work, manufacture completion or return references. */
static INT __attribute__((unused)) wr_iot_physical_initial_query_owned(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_initial_request *request,
 unsigned char *wire,unsigned int length)
{
 struct wr_iot_physical_stop_lifetime life;
 ULONG flags=0;unsigned i;int exact,encoded=0;
 if(!wire||length!=64)return -EINVAL;
 for(i=0;i<length;i++)wire[i]=0;
 if(!ad||!main_dev||!wr_iot_physical_initial_valid(request,0)||
    request->action!=WR_STOP_QUERY)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 life=ad->wr_iot_physical_lifetime;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 exact=wr_iot_physical_initial_main_binding(
   &ad->wr_iot_physical_initial.origin,&life)&&
  ad->wr_iot_physical_initial.origin.main_device==main_dev&&
  ad->wr_iot_physical_pins.module==1&&
  ad->wr_iot_physical_pins.task==current&&
  ad->wr_iot_physical_pins.device==(struct net_device *)main_dev;
 if(exact)encoded=wr_iot_physical_initial_record_reply(
  &ad->wr_iot_physical_initial,request,current,wire,length);
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 return encoded?0:-EAGAIN;
}
