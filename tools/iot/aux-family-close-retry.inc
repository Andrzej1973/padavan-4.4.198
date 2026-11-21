/* Direct continuation only. Caller must pin adapter/netdev and serialize
 * with RTNL. No worker is queued here and no family/HNAT effect is replayed. */
static inline INT wr_iot_aux_family_close_retry_owned(RTMP_ADAPTER *ad,PNET_DEV dev,
 enum wr_iot_ref_family family)
{
 struct wr_iot_interface_ref *r=NULL;
 struct wr_iot_family_close *state;
 struct wr_iot_radio_ticket ticket;
 unsigned int i,slot=0;unsigned long generation=0;
 ULONG flags;int admitted,result,unmutated,consumed;
 if(!ad||!dev||(family!=WR_REF_FAMILY_APCLI&&family!=WR_REF_FAMILY_MONITOR))return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 for(i=0;i<WDEV_NUM_MAX+1;i++)if(ad->wr_iot_interface_refs[i].device==dev){
  if(r)goto reject;
  r=&ad->wr_iot_interface_refs[i];slot=i;
 }
 if(!r||r->family!=family)goto reject;
 state=&ad->wr_iot_family_close[slot];
 if(state->phase!=WR_FAMILY_DOWN_RETRY||!wr_iot_family_close_matches(state,r))goto reject;
 admitted=wr_iot_aux_close_retry_unmutated_down(&ad->wr_iot_transition,
  ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,family,VIRTUAL_IF_NUM(ad),&ticket,&generation);
 if(!admitted||!wr_iot_family_down_begin(state,r))goto reject;
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 result=wr_iot_virtual_down_checked(ad,&ticket);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 if(result!=NDIS_STATUS_SUCCESS){
  unmutated=ad->wr_iot_transition.virtual_down_stage==0&&
   ad->wr_iot_transition.epoch==ticket.epoch&&ad->wr_iot_transition.serial==ticket.serial&&
   VIRTUAL_IF_NUM(ad)==r->close_vendor_count;
  if(unmutated)unmutated=wr_iot_aux_close_retry_release(&ad->wr_iot_transition,
    ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket);
  (void)wr_iot_family_down_result(state,r,0,unmutated);
  if(!unmutated)r->close_stage=6;
  goto reject;
 }
 if(!wr_iot_family_down_result(state,r,1,0)||!wr_iot_family_close_finish(state,r))goto reject;
 consumed=wr_iot_aux_close_finalize_after_down(&ad->wr_iot_transition,
  ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation,&ticket,3,VIRTUAL_IF_NUM(ad));
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!consumed)return -EBUSY;
 wake_up_all(&ad->wr_iot_ticket_wait);RT_MOD_DEC_USE_COUNT();return 0;
reject:
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);return -EBUSY;
}
