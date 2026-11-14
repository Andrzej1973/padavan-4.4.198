/* Read-only old-origin correlation for future restart admission. Caller holds
 * transition lock and outer adapter lifetime; no OPEN permission is issued. */
#ifndef WR_IOT_PHYSICAL_STOP_ORIGIN_H
#define WR_IOT_PHYSICAL_STOP_ORIGIN_H
#include "physical-stop-terminal-types.h"
#include "physical-stop-response.h"
#include "main-open-recovery-owner.h"
static inline int wr_iot_physical_stop_origin_matches(
 const struct wr_iot_physical_stop_origin *s,
 const struct wr_iot_main_recovery_release_receipt *r)
{
 if(!s||!r||s->valid!=1||r->valid!=1||!r->device||
    !s->main_generation||!s->main_open_token||!s->arm_epoch||
    !s->ticket_serial||!s->ticket_epoch||!s->completion_epoch||
    !r->close_serial||r->ticket.operation!=WR_RADIO_CLOSE||r->ticket.reset_kind)return 0;
 return s->main_generation==r->generation&&s->main_open_token==r->open_token&&
  s->ticket_serial==r->ticket.serial&&s->ticket_epoch==r->ticket.epoch&&
  s->completion_epoch==r->completion_epoch&&s->ticket_epoch>s->arm_epoch&&
  s->completion_epoch>=s->ticket_epoch;
}
/* Same-registration Main reopen only. A replacement adapter/registration needs
 * its own distinct handoff; address reuse never satisfies this predicate.
 * This checks Main software state, not ra2 readiness or RF/DMA retirement. */
static inline int wr_iot_physical_stop_origin_main_ready(
 const struct wr_iot_physical_stop_origin *origin,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *main_record)
{
 if(!origin||!owner||!radio||!main_record||
    !wr_iot_physical_stop_origin_matches(origin,&owner->last_release)||
    owner->phase!=WR_MAIN_OWNER_IDLE||owner->deferred_owners||
    owner->netdev_release_started||owner->device||
    radio->phase!=WR_RADIO_READY||!radio->main_ready||radio->busy||radio->active_tx||
    radio->reset_pending||radio->retiring||radio->exhausted||radio->main_inhibited||
    radio->pm_suspending||radio->pm_suspended||
    radio->epoch<=origin->completion_epoch||radio->serial<=origin->ticket_serial||
    radio->serial!=radio->retired_serial)return 0;
 return main_record->device==owner->last_release.device&&
  main_record->family==WR_REF_FAMILY_MAIN&&main_record->published==1&&
  !main_record->removing&&!main_record->removal_stage&&
  main_record->phase==WR_REF_OWNED&&main_record->generation==origin->main_generation&&
  main_record->last_token>origin->main_open_token&&!main_record->close_running&&
  !main_record->close_uncertain_reason;
}
/* Historical ra2 CLOSE identity only, deliberately not current-epoch CLOSED
 * admission. Fresh beacon/key/probe and exact issuer still need validation. */
static inline int wr_iot_physical_stop_origin_iot_history(
 const struct wr_iot_physical_stop_request *request,
 const struct wr_iot_interface_ref *record,const void *iot_device)
{
 if(!wr_iot_physical_stop_request_valid(request)||request->action!=WR_STOP_RELEASE||
    !record||!iot_device||record->device!=iot_device||
    record->family!=WR_REF_FAMILY_MBSS||record->published!=1||
    record->removing||record->removal_stage||record->phase!=WR_REF_IDLE||
    record->open_unmutated||record->close_running||record->close_uncertain_reason||
    record->close_stage!=4U)return 0;
 return record->generation==request->generation&&record->last_token==request->open_token&&
  record->close_serial==request->closed_serial&&record->close_epoch==request->epoch;
}
/* Rebind preflight composes actual new Main readiness with old ra2 history.
 * It preserves the old close_epoch. Current hardware configuration observation
 * must run under its own admitted BSS_OBSERVE ticket before OPEN admission. */
static inline int wr_iot_physical_stop_origin_pair(
 const struct wr_iot_physical_stop_terminal *terminal,
 const struct pid *issuer,const struct wr_iot_physical_stop_request *request,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_device,const void *iot_device,unsigned int vendor_count)
{
 struct wr_iot_interface_ref *main_record,*iot_record;unsigned i;
 if(!terminal||terminal->ready!=1||terminal->status!=WR_STOP_RELEASED||
    !issuer||terminal->owner!=issuer||!wr_iot_physical_stop_request_valid(request)||
    request->action!=WR_STOP_RELEASE||request->attempt!=terminal->request.attempt||
    request->epoch!=terminal->request.epoch||request->generation!=terminal->request.generation||
    request->open_token!=terminal->request.open_token||
    request->closed_serial!=terminal->request.closed_serial||
    !slots||!count||!main_device||!iot_device||main_device==iot_device||
    !wr_iot_physical_stop_request_valid(&terminal->request)||
    terminal->request.action!=WR_STOP_RELEASE||!vendor_count)return 0;
 for(i=0;i<sizeof(request->nonce);i++)
  if(request->nonce[i]!=terminal->request.nonce[i])return 0;
 main_record=wr_iot_registry_find_owned(slots,count,main_device);
 iot_record=wr_iot_registry_find(slots,count,iot_device,terminal->request.generation);
 return wr_iot_physical_stop_origin_main_ready(&terminal->origin,owner,radio,main_record)&&
  wr_iot_physical_stop_origin_iot_history(&terminal->request,iot_record,iot_device)&&
  wr_iot_registry_count_matches(slots,count,vendor_count);
}
#endif
