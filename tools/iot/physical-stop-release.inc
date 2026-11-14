/* Caller owns RTNL/outer adapter lifetime and persistent terminal storage.
 * No physical teardown or waits. RELEASE requires exact checked Main completion.
 * Terminal is prepared before mutation, committed only after actual puts/end.
 * Include after admission, pins and terminal helpers. */
#include "physical-stop-origin.h"
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
 if(exact){
  /* Preserve the checked old Main identity before lifetime_end clears it.
   * Derive solely from actual driver state, under the existing disjoint lock;
   * the cached request/PID binds this receipt to its original transaction. */
  RTMP_IRQ_LOCK(&ad->wr_iot_transition_lock,flags);
  {
   const struct wr_iot_physical_stop_lifetime *s=&ad->wr_iot_physical_lifetime;
   struct wr_iot_interface_ref *main_record=wr_iot_registry_find(
    ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,main_dev,s->main_generation);
   exact=s->main_device==main_dev&&
    wr_iot_physical_stop_lifetime_main_released(s,serial,&ad->wr_iot_main_recovery,
     &ad->wr_iot_transition,main_record,VIRTUAL_IF_NUM(ad))&&
    s->main_generation&&s->main_open_token&&s->arm_radio_epoch&&
    s->main_ticket.serial&&s->main_ticket.epoch&&ad->wr_iot_transition.epoch;
   if(exact){
    terminal->origin.main_generation=s->main_generation;
    terminal->origin.main_open_token=s->main_open_token;
    terminal->origin.arm_epoch=s->arm_radio_epoch;
    terminal->origin.ticket_serial=s->main_ticket.serial;
    terminal->origin.ticket_epoch=s->main_ticket.epoch;
    terminal->origin.completion_epoch=ad->wr_iot_transition.epoch;
    terminal->origin.valid=1;
    exact=wr_iot_physical_stop_origin_matches(&terminal->origin,
     &ad->wr_iot_main_recovery.last_release);
   }
  }
  RTMP_IRQ_UNLOCK(&ad->wr_iot_transition_lock,flags);
 }
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
