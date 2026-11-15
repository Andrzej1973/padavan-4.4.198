/* Candidate serialized terminal wrapper. Caller holds RTNL and an independent
 * adapter/module lifetime through this entire call, including native puts.
 * Cache and pending bundle must live in adapter-owned persistent storage. */
static INT __attribute__((unused)) wr_iot_physical_initial_cleanup(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_initial_request *request,
 struct wr_iot_physical_initial_terminal *terminal)
{
 struct wr_iot_physical_initial_record observed;
 struct wr_iot_interface_ref *main_record,*iot_record;
 struct wr_iot_physical_stop_lifetime *life;
 ULONG flags=0;int exact,detached,ended;
 if(!ad||!main_dev||!terminal||!wr_iot_physical_initial_valid(request,0)||
    (request->action!=WR_STOP_CANCEL&&request->action!=WR_STOP_RELEASE))return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(terminal->owner){
  if(!wr_iot_physical_initial_terminal_matches(terminal,request))return -EBUSY;
  if(terminal->ready)return 0;
 }else if(!wr_iot_physical_initial_terminal_prepare(terminal,request))return -ENOMEM;
 if(!terminal->cleanup_phase){
  RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
  observed=ad->wr_iot_physical_initial;
  exact=wr_iot_physical_initial_record_matches(&observed,request,current);
  RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
  if(!exact)return -EAGAIN;
  if(request->action==WR_STOP_RELEASE){
   if(wr_iot_physical_initial_main_complete(ad,main_dev,request->attempt))return -EAGAIN;
  }else{
   RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
   exact=observed.origin.main_device==main_dev&&
    wr_iot_physical_initial_cancel_current(&observed.origin,&ad->wr_iot_physical_lifetime,
     &ad->wr_iot_idle_probe,&ad->wr_iot_main_recovery,&ad->wr_iot_transition,
     ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad));
   RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
   if(!exact)return -EAGAIN;
  }
  RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
  detached=wr_iot_physical_initial_pins_detach(&ad->wr_iot_physical_pins,
   &ad->wr_iot_physical_pending_pins,&ad->wr_iot_physical_initial,request);
  if(detached)terminal->cleanup_phase=1;
  RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
  if(!detached)return -EAGAIN;
 }
 if(terminal->cleanup_phase==1){
  if(!wr_iot_physical_stop_pins_drop(&ad->wr_iot_physical_pending_pins))return -EUCLEAN;
  terminal->cleanup_phase=2;
 }
 if(terminal->cleanup_phase==2){
  RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
  observed=ad->wr_iot_physical_initial;
  exact=!observed.task&&observed.serial==request->attempt&&
   !ad->wr_iot_physical_pins.module&&!ad->wr_iot_physical_pins.task&&
   !ad->wr_iot_physical_pins.device&&!ad->wr_iot_physical_pending_pins.module&&
   !ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device;
  RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
  if(!exact)return -EUCLEAN;
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  life=&ad->wr_iot_physical_lifetime;
  main_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   main_dev,observed.origin.main_generation);
  iot_record=wr_iot_registry_find(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,
   ad->ApCfg.MBSSID[2].wdev.if_dev,observed.origin.generation);
  exact=request->action==WR_STOP_CANCEL?
   wr_iot_physical_initial_cancel_current(&observed.origin,life,&ad->wr_iot_idle_probe,
    &ad->wr_iot_main_recovery,&ad->wr_iot_transition,ad->wr_iot_interface_refs,
    WDEV_NUM_MAX+1,VIRTUAL_IF_NUM(ad)):
   wr_iot_physical_initial_main_released(&observed.origin,life,&ad->wr_iot_main_recovery,
    &ad->wr_iot_transition,main_record,iot_record,VIRTUAL_IF_NUM(ad));
  ended=exact&&wr_iot_physical_stop_lifetime_end(life,observed.origin.lifetime_serial,1,1);
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
  if(!ended)return -EAGAIN;
  terminal->cleanup_phase=3;
 }
 if(terminal->cleanup_phase!=3)return -EUCLEAN;
 /* RTNL serializes terminal publication; all referenced mutable owners are
  * now detached/ended, no kernel operation occurs inside commit. */
 return wr_iot_physical_initial_terminal_commit(terminal,&ad->wr_iot_physical_initial,
  &ad->wr_iot_physical_lifetime,&ad->wr_iot_physical_pins,
  &ad->wr_iot_physical_pending_pins)?0:-EUCLEAN;
}
