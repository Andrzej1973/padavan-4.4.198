/* Read-only old-origin correlation for future restart admission. Caller holds
 * transition lock and outer adapter lifetime; no OPEN permission is issued. */
#ifndef WR_IOT_PHYSICAL_STOP_ORIGIN_H
#define WR_IOT_PHYSICAL_STOP_ORIGIN_H
#include "physical-stop-terminal-types.h"
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
#endif
