/* Locked reference-only completion observation. Does not release API owner,
 * resources or network isolation, and is not RF/FIFO/late-callback proof. */
#ifndef WR_IOT_DRIVER_API_CLOSE_COMPLETION_H
#define WR_IOT_DRIVER_API_CLOSE_COMPLETION_H
#include "driver-api-close-owner.h"
#include "mbss-close-receipt.h"
static inline int wr_iot_driver_close_reference_completed(
 const struct wr_iot_driver_close_owner *owner,const void *task,const void *dev,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,unsigned int vendor_count)
{
 struct wr_iot_interface_ref *record;
 if(!owner||!task||!dev||!radio||!owner->active||!owner->consumed||
    owner->task!=task||owner->device!=dev||
    owner->ticket.operation!=WR_RADIO_BSS_CLOSE||owner->ticket.reset_kind||
    radio->epoch!=owner->ticket.epoch||
    radio->retired_serial!=owner->ticket.serial)return 0;
 record=wr_iot_registry_find(slots,count,dev,owner->generation);
 if(!record||record->close_epoch!=owner->ticket.epoch||
    record->close_serial!=owner->ticket.serial||
    !record->close_vendor_count||record->close_vendor_count-1!=vendor_count||
    record->close_prior_phase!=(int)owner->ticket.prior_phase||
    record->close_prior_ready!=owner->ticket.prior_ready)return 0;
 return wr_iot_mbss_closed_reference(radio,slots,count,main_dev,dev,
  owner->generation,owner->open_token,owner->ticket.serial,vendor_count);
}
#endif
