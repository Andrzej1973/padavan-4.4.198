/* Linux-only never-opened origin, distinct from released IoT CLOSE.
 * Caller holds transition lock and actual Main lifetime/RTNL pins. This records
 * provenance only: no ARM endpoint, hardware completion or teardown permission.
 * Peer-table/executor exclusion is checked separately under MacTabLock. */
#ifndef WR_IOT_PHYSICAL_INITIAL_ORIGIN_H
#define WR_IOT_PHYSICAL_INITIAL_ORIGIN_H
#include "precreated-idle-probe.h"
#include "physical-stop-lifetime.h"
#include "physical-initial-types.h"
static inline int wr_iot_physical_initial_history(
 const struct wr_iot_physical_initial_origin *s,const struct wr_iot_interface_ref *r)
{
 return s&&s->main_device&&s->iot_device&&s->epoch&&s->generation&&s->idle_serial&&
  s->main_generation&&s->main_open_token&&s->lifetime_serial&&r&&
  r->device==s->iot_device&&r->generation==s->generation&&
  r->family==WR_REF_FAMILY_MBSS&&r->published&&!r->removing&&!r->removal_stage&&
  r->phase==WR_REF_IDLE&&!r->last_token&&!r->open_unmutated&&
  !r->close_serial&&!r->close_epoch&&!r->close_stage&&!r->close_running&&
  !r->close_uncertain_reason&&!r->close_vendor_count&&!r->close_verified_stage&&
  !r->close_prior_phase&&!r->close_prior_ready;
}
static inline int wr_iot_physical_initial_capture(
 struct wr_iot_physical_initial_origin *s,
 const struct wr_iot_precreated_idle_probe *probe,
 const struct wr_iot_physical_stop_lifetime *life,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned count,const void *main_dev,const void *iot_dev,
 unsigned long generation,unsigned vendor_count)
{
 struct wr_iot_physical_initial_origin next={0};
 struct wr_iot_interface_ref *main;
 if(!s||s->main_device||s->iot_device||s->epoch||s->generation||s->idle_serial||
    s->main_generation||s->main_open_token||s->lifetime_serial||!life||
    !life->active||!life->serial||life->main_device!=main_dev||
    !life->main_generation||!life->main_open_token||life->main_ticket_valid||
    life->arm_record_serial||life->arm_request.action||!radio||radio->active_tx||
    life->arm_radio_epoch!=radio->epoch||life->arm_radio_serial!=radio->serial||
    radio->serial!=radio->retired_serial||
    !wr_iot_precreated_idle_probe_current(probe,radio,slots,count,
     main_dev,iot_dev,generation,vendor_count))return 0;
 main=wr_iot_registry_find_owned(slots,count,main_dev);
 if(!main||main->generation!=life->main_generation||
    main->last_token!=life->main_open_token)return 0;
 next.main_device=main_dev;next.iot_device=iot_dev;next.epoch=probe->ticket.epoch;
 next.generation=generation;next.idle_serial=probe->ticket.serial;
 next.main_generation=life->main_generation;next.main_open_token=life->main_open_token;
 next.lifetime_serial=life->serial;*s=next;return 1;
}
/* Main may be DOWN now: do not call the live READY-only idle predicate.
 * Exact Main release must be proved independently by its lifetime checker. */
static inline int wr_iot_physical_initial_main_binding(
 const struct wr_iot_physical_initial_origin *s,
 const struct wr_iot_physical_stop_lifetime *life)
{
 return s&&life&&s->main_device&&s->iot_device&&s->epoch&&s->idle_serial&&
  life->active&&life->serial==s->lifetime_serial&&
  life->main_device==s->main_device&&life->main_generation==s->main_generation&&
  life->main_open_token==s->main_open_token&&life->arm_radio_epoch==s->epoch&&
  life->arm_radio_serial==s->idle_serial;
}
/* Transition lock only. Native Main completion includes exact callback and
 * dev_put receipts; peer-table/executor and hardware stage checks remain
 * separate MacTabLock obligations in the eventual ARM/QUERY binding. */
static inline int wr_iot_physical_initial_main_released(
 const struct wr_iot_physical_initial_origin *s,
 const struct wr_iot_physical_stop_lifetime *life,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *main,const struct wr_iot_interface_ref *iot,
 unsigned vendor_count)
{
 return wr_iot_physical_initial_main_binding(s,life)&&
  wr_iot_physical_initial_history(s,iot)&&radio&&radio->epoch>s->epoch&&
  wr_iot_physical_stop_lifetime_main_released(life,s->lifetime_serial,
   owner,radio,main,vendor_count);
}
/* CANCEL preflight under transition lock. An ARMED record alone cannot
 * authorize cancellation once Main's close/recovery ticket has been admitted. */
static inline int wr_iot_physical_initial_cancel_current(
 const struct wr_iot_physical_initial_origin *s,
 const struct wr_iot_physical_stop_lifetime *life,
 const struct wr_iot_precreated_idle_probe *probe,
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned count,unsigned vendor_count)
{
 struct wr_iot_interface_ref *main;
 if(!wr_iot_physical_initial_main_binding(s,life)||life->main_ticket_valid||
    !owner||owner->phase!=WR_MAIN_OWNER_IDLE||owner->deferred_owners||
    owner->netdev_release_started||owner->device||!radio||radio->active_tx||
    radio->epoch!=s->epoch||radio->serial!=s->idle_serial||
    !wr_iot_precreated_idle_probe_current(probe,radio,slots,count,
     s->main_device,s->iot_device,s->generation,vendor_count))return 0;
 main=wr_iot_registry_find_owned(slots,count,s->main_device);
 return main&&main->generation==s->main_generation&&
  main->last_token==s->main_open_token&&!main->close_running&&
  !main->close_uncertain_reason;
}
#endif
