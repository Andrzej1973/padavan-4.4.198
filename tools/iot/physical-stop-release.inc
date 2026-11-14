/* Caller owns RTNL/outer adapter lifetime and persistent terminal storage.
 * No physical teardown or waits. RELEASE requires exact checked Main completion.
 * Terminal is prepared before mutation, committed only after actual puts/end.
 * Include after admission, pins and terminal helpers. */
static INT __attribute__((unused)) wr_iot_physical_stop_release_owned(
 RTMP_ADAPTER *ad,PNET_DEV main_dev,
 const struct wr_iot_physical_stop_request *request,unsigned long serial,
 struct wr_iot_physical_stop_terminal *terminal)
{
 ULONG flags=0;int exact,detached,idle,returned,ended;
 if(!ad||!main_dev||!serial||!terminal||
    !wr_iot_physical_stop_request_valid(request)||request->action!=WR_STOP_RELEASE)
  return -EINVAL;
 if(terminal!=&ad->wr_iot_physical_terminal)return -EINVAL;
 if(!rtnl_is_locked())return -EBUSY;
 if(!wr_iot_physical_stop_terminal_prepare(terminal,request))return -EBUSY;
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 {
  const struct wr_iot_physical_stop_lifetime *s=&ad->wr_iot_physical_lifetime;
  exact=s->active&&s->serial==serial&&s->arm_request.action==WR_STOP_ARM&&
   s->arm_record_serial!=~0ULL&&request->attempt==s->arm_record_serial+1&&
   request->epoch==s->arm_request.epoch&&request->generation==s->arm_request.generation&&
   request->open_token==s->arm_request.open_token&&
   request->closed_serial==s->arm_request.closed_serial&&
   wr_iot_physical_stop_nonce_equal(request->nonce,s->arm_request.nonce);
 }
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(exact)exact=wr_iot_physical_stop_main_complete(ad,main_dev,serial)==0;
 if(!exact){wr_iot_physical_stop_terminal_clear(terminal);return -EAGAIN;}
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 detached=wr_iot_physical_stop_pins_detach(&ad->wr_iot_physical_pins,
  &ad->wr_iot_physical_pending_pins,&ad->wr_iot_physical_stop,request->attempt,
  request->epoch,request->generation,request->nonce,0);
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 if(!detached){wr_iot_physical_stop_terminal_clear(terminal);return -EBUSY;}
 returned=wr_iot_physical_stop_pins_drop(&ad->wr_iot_physical_pending_pins);
 if(!returned)return -EUCLEAN; /* persistent references/cache remain owned */
 RTMP_IRQ_LOCK(&ad->MacTabLock,flags);
 idle=!wr_iot_physical_stop_blocks_retirement(&ad->wr_iot_physical_stop,
    &ad->wr_iot_physical_pins)&&!ad->wr_iot_physical_pending_pins.module&&
    !ad->wr_iot_physical_pending_pins.task&&!ad->wr_iot_physical_pending_pins.device;
 RTMP_IRQ_UNLOCK(&ad->MacTabLock,flags);
 RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
 ended=wr_iot_physical_stop_lifetime_end(&ad->wr_iot_physical_lifetime,serial,idle,returned);
 RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 if(!wr_iot_physical_stop_terminal_commit(terminal,idle,returned,ended))return -EUCLEAN;
 return 0;
}
