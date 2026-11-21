/* Extra netdev reference return for synchronous reference-complete CLOSE.
 * Caller pins registration/adapter under RTNL and keeps API module hold.
 * No recovery ownership transfer or RF/reopen authority is fabricated. */
#ifndef WR_IOT_DRIVER_API_CLOSE_SYNCHRONOUS_PUT_H
#define WR_IOT_DRIVER_API_CLOSE_SYNCHRONOUS_PUT_H
#include "driver-api-close-join.h"
#include "mbss-close-receipt.h"
static inline int wr_iot_driver_close_synchronous_put_claim(
 struct wr_iot_driver_close_owner *close,const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,const void *main_dev,
 unsigned int vendor_count,struct wr_iot_driver_close_join_receipt *receipt)
{
 struct wr_iot_interface_ref *record;
 if(!close||!receipt||!radio||!close->active||!close->consumed||close->task||
    !close->reference_completed||close->uncertain||!close->module_held||
    !close->netdev_held||close->retirement_module_transferred||
    close->recovery_netdev_transferred||close->recovery_join_pending||
    close->recovery_netdev_returned||close->synchronous_put_pending||
    close->synchronous_netdev_returned||close->retirement_task||
    close->retirement_started||close->retirement_entered||close->retirement_canceling||
    close->ticket.operation!=WR_RADIO_BSS_CLOSE||close->ticket.reset_kind||
    radio->epoch!=close->ticket.epoch||radio->retired_serial!=close->ticket.serial||
    !wr_iot_mbss_closed_reference(radio,slots,count,main_dev,close->device,
      close->generation,close->open_token,close->ticket.serial,vendor_count))return 0;
 record=wr_iot_registry_find(slots,count,close->device,close->generation);
 if(!record||!wr_iot_mbss_recovery_ticket_recorded(record,&close->ticket))return 0;
 receipt->device=close->device;receipt->generation=close->generation;
 receipt->open_token=close->open_token;receipt->epoch=close->ticket.epoch;
 receipt->serial=close->ticket.serial;
 close->netdev_held=0;close->synchronous_put_pending=1;return 1;
}
static inline int wr_iot_driver_close_synchronous_put_returned(
 struct wr_iot_driver_close_owner *close,
 const struct wr_iot_driver_close_join_receipt *receipt)
{
 if(!close||!receipt||!close->active||!close->consumed||close->task||
    !close->reference_completed||close->uncertain||!close->module_held||close->netdev_held||
    !close->synchronous_put_pending||close->synchronous_netdev_returned||
    close->recovery_netdev_transferred||close->recovery_join_pending||close->recovery_netdev_returned||
    close->device!=receipt->device||close->generation!=receipt->generation||
    close->open_token!=receipt->open_token||close->ticket.epoch!=receipt->epoch||
    close->ticket.serial!=receipt->serial)return 0;
 close->synchronous_put_pending=0;close->synchronous_netdev_returned=1;return 1;
}
#endif
