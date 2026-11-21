/* RTNL and registration/module lifetime must span claim, real dev_put and ack.
 * On ack drift keep pending fence: never retry dev_put or restore a spent hold. */
static INT wr_iot_driver_close_synchronous_put(RTMP_ADAPTER *ad,PNET_DEV dev)
{
 struct wr_iot_driver_close_join_receipt receipt={0};ULONG flags=0;int claimed,returned;
 if(!ad||!dev||!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 claimed=ad->wr_iot_close_owner.device==dev&&
  wr_iot_driver_close_synchronous_put_claim(&ad->wr_iot_close_owner,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->net_dev,VIRTUAL_IF_NUM(ad),&receipt);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!claimed)return -EBUSY;
 dev_put(dev);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 returned=wr_iot_driver_close_synchronous_put_returned(&ad->wr_iot_close_owner,&receipt);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 return returned?0:-EUCLEAN;
}
