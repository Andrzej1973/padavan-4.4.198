/* Synchronous RTNL CANCEL-only replacement. Move old PID cache ownership;
 * restore record/cache on admission refusal, drop old PID only after success. */
static INT __attribute__((unused)) wr_iot_physical_initial_arm_replace_terminal(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_initial_request *request,unsigned long *serial)
{
 struct wr_iot_physical_initial_terminal old={0},empty_cache={0};
 struct wr_iot_physical_initial_record prior,empty_record={0};
 struct wr_iot_physical_initial_response match;
 struct wr_iot_interface_ref *main_record,*iot_record;
 ULONG flags=0;int exact,status;unsigned i,nonce_difference=0;
 if(serial)*serial=0;
 if(!ad||!main_dev||!serial||!wr_iot_physical_initial_valid(request,0)||
    request->action!=WR_STOP_ARM)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 prior=ad->wr_iot_physical_initial;
 if(!ad->wr_iot_physical_initial_terminal.owner){
  RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
  return wr_iot_physical_initial_arm_admit(ad,main_dev,request,serial);
 }
 old=ad->wr_iot_physical_initial_terminal; /* borrowed until explicit move */
 for(i=0;i<16;i++)nonce_difference|=old.request.nonce[i]^request->nonce[i];
 match.identity=prior.request;match.identity.action=WR_STOP_CANCEL;
 match.identity.attempt=prior.serial;match.status=WR_STOP_CANCELLED;
 exact=old.owner==task_pid(current)&&old.ready&&old.cleanup_phase==3&&
  old.status==WR_STOP_CANCELLED&&old.request.action==WR_STOP_CANCEL&&
  nonce_difference&&wr_iot_physical_initial_reply_matches(&match,&old.request)&&
  !prior.task&&prior.status==WR_STOP_ARMED&&!prior.completion_epoch&&
  !ad->wr_iot_physical_pins.module&&!ad->wr_iot_physical_pins.task&&
  !ad->wr_iot_physical_pins.device&&!ad->wr_iot_physical_pending_pins.module&&
  !ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!exact)return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 main_record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev);
 iot_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->ApCfg.MBSSID[2].wdev.if_dev,prior.origin.generation);
 exact=!ad->wr_iot_physical_lifetime.active&&
  ad->wr_iot_physical_lifetime.serial==prior.origin.lifetime_serial&&
  prior.origin.main_device==main_dev&&main_record&&
  main_record->generation==prior.origin.main_generation&&
  main_record->last_token==prior.origin.main_open_token&&
  ad->wr_iot_transition.epoch==prior.origin.epoch&&
  wr_iot_physical_initial_history(&prior.origin,iot_record);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!exact)return -EAGAIN;
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 /* RTNL serializes all cache/terminal mutations; no live initial task exists. */
 ad->wr_iot_physical_initial_terminal=empty_cache;
 empty_record.serial=prior.serial;ad->wr_iot_physical_initial=empty_record;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 status=wr_iot_physical_initial_arm_admit(ad,main_dev,request,serial);
 if(status){
  RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
  ad->wr_iot_physical_initial=prior;ad->wr_iot_physical_initial_terminal=old;
  RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
  return status;
 }
 wr_iot_physical_initial_terminal_clear(&old);
 return 0;
}
