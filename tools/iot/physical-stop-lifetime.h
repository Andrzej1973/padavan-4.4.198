/* Adapter transition-lock-only exclusion spanning MacTabLock record/pin work.
 * No nested locks. This is software lifetime admission, never RF/DMA proof. */
#ifndef WR_IOT_PHYSICAL_STOP_LIFETIME_H
#define WR_IOT_PHYSICAL_STOP_LIFETIME_H
#include "radio-transition.h"
#include "physical-stop-wire.h"
#include "main-open-recovery-owner.h"
struct wr_iot_physical_stop_lifetime {
 unsigned long serial;unsigned int active;
 const void *main_device;
 unsigned long main_generation,main_open_token,arm_radio_serial,arm_radio_epoch;
 unsigned long long arm_record_serial;
 struct wr_iot_physical_stop_request arm_request;
 struct wr_iot_radio_ticket main_ticket;
 int main_ticket_valid;
};
static inline unsigned long wr_iot_physical_stop_lifetime_begin(
 struct wr_iot_physical_stop_lifetime *s,const struct wr_iot_radio_transition *radio)
{
 if(!s||!radio||s->active||s->serial==~0UL||radio->retiring||radio->busy||
    radio->active_tx||radio->reset_pending||radio->pm_suspending||radio->pm_suspended||
    radio->exhausted||radio->phase!=WR_RADIO_READY||!radio->main_ready)return 0;
 s->serial++;s->active=1;
 s->main_device=0;s->main_generation=s->main_open_token=s->arm_radio_serial=0;
 s->arm_radio_epoch=s->arm_record_serial=0;s->arm_request.action=0;
 s->main_ticket_valid=0;
 return s->serial;
}
/* Actual caller must hold transition lock over registry validation and fence
 * admission. No caller-provided identity is accepted as the Main snapshot. */
static inline unsigned long wr_iot_physical_stop_lifetime_begin_main(
 struct wr_iot_physical_stop_lifetime *s,const struct wr_iot_radio_transition *radio,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_interface_ref *main_record,const void *main_device){
 unsigned long serial;
 /* READY -> main_down -> physical CLOSING consumes two epoch increments.
  * Refuse before acquiring this fence when that exact close cannot be issued. */
 if(!radio||radio->serial!=radio->retired_serial||
    radio->serial==~0UL||radio->epoch>~0UL-2UL||
    !owner||owner->phase!=WR_MAIN_OWNER_IDLE||owner->deferred_owners||
    owner->netdev_release_started||!main_record||!main_device||
    main_record->device!=main_device||main_record->family!=WR_REF_FAMILY_MAIN||
    !main_record->published||main_record->removing||
    main_record->phase!=WR_REF_OWNED||!main_record->generation||
    !main_record->last_token||main_record->open_unmutated)return 0;
 serial=wr_iot_physical_stop_lifetime_begin(s,radio);
 if(!serial)return 0;
 s->main_device=main_device;s->main_generation=main_record->generation;
 s->main_open_token=main_record->last_token;s->arm_radio_serial=radio->serial;
 s->arm_radio_epoch=radio->epoch;
 return serial;
}
static inline int wr_iot_physical_stop_lifetime_capture_main(
 struct wr_iot_physical_stop_lifetime *s,unsigned long serial,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *record,struct wr_iot_radio_ticket *out){
 struct wr_iot_radio_ticket captured;
 if(!s||!s->active||!serial||s->serial!=serial||!record||!out||
    !s->main_device||record->device!=s->main_device)return 0;
 if(!wr_iot_main_recovery_capture_physical_ticket(owner,radio,record,
    s->arm_radio_serial,s->main_generation,s->main_open_token,&captured))return 0;
 if(s->main_ticket_valid&&
    (s->main_ticket.serial!=captured.serial||s->main_ticket.epoch!=captured.epoch||
     s->main_ticket.prior_phase!=captured.prior_phase||
     s->main_ticket.prior_ready!=captured.prior_ready))return 0;
 s->main_ticket=captured;s->main_ticket_valid=1;*out=captured;return 1;
}
/* Recovery may finish before the first QUERY. Recover only the durable exact
 * Main release for the ARM-time OPEN, never whichever completed owner exists.
 * Caller holds transition lock and has maintained this lifetime fence. */
static inline int wr_iot_physical_stop_lifetime_capture_released_main(
 struct wr_iot_physical_stop_lifetime *s,unsigned long serial,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *record,unsigned int vendor_count){
 const struct wr_iot_main_recovery_release_receipt *r;
 if(!s||!s->active||!serial||s->serial!=serial||!owner||!record||
    !s->main_device||record->device!=s->main_device||
    !wr_iot_main_recovery_release_current(owner,radio,record,vendor_count))
  return 0;
 r=&owner->last_release;
 if(r->generation!=s->main_generation||r->open_token!=s->main_open_token||
    r->ticket.serial<=s->arm_radio_serial||
    r->ticket.operation!=WR_RADIO_CLOSE||r->ticket.reset_kind)return 0;
 if(s->main_ticket_valid&&
    (s->main_ticket.serial!=r->ticket.serial||
     s->main_ticket.epoch!=r->ticket.epoch||
     s->main_ticket.prior_phase!=r->ticket.prior_phase||
     s->main_ticket.prior_ready!=r->ticket.prior_ready))return 0;
 s->main_ticket=r->ticket;s->main_ticket_valid=1;return 1;
}
/* Consume the captured ticket after the worker/reaper owner is reset. */
static inline int wr_iot_physical_stop_lifetime_main_released(
 const struct wr_iot_physical_stop_lifetime *s,unsigned long serial,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *record,unsigned int vendor_count){
 if(!s||!s->active||!serial||s->serial!=serial||!s->main_ticket_valid||
    !record||record->device!=s->main_device)return 0;
 return wr_iot_main_recovery_release_for_ticket(owner,radio,record,vendor_count,
  &s->main_ticket,s->main_generation,s->main_open_token);
}
/* Clear only after exact record cancel/release AND actual reference returns.
 * A failed partial arm may clear only after its local refs are returned too.
 * Booleans are binding receipts, not permission supplied by userspace. */
static inline int wr_iot_physical_stop_lifetime_end(
 struct wr_iot_physical_stop_lifetime *s,unsigned long serial,
 int record_idle,int pins_returned)
{
 if(!s||!s->active||!serial||s->serial!=serial||record_idle!=1||pins_returned!=1)return 0;
 s->active=0;s->main_device=0;s->main_ticket_valid=0;
 s->main_generation=s->main_open_token=s->arm_radio_serial=0;
 s->arm_radio_epoch=s->arm_record_serial=0;s->arm_request.action=0;return 1;
}
static inline int wr_iot_physical_stop_lifetime_blocks(
 const struct wr_iot_physical_stop_lifetime *s)
{return !s||s->active;}
#endif
