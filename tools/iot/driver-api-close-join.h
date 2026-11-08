/* Locked exact recovery netdev-return accounting only. External exclusive
 * reaper must join work before claim, execute dev_put, then acknowledge with
 * the captured identity. Neither helper drops a ref or retires API owner.
 * No RF, buffer reuse, isolation removal or module release permission. */
#ifndef WR_IOT_DRIVER_API_CLOSE_JOIN_H
#define WR_IOT_DRIVER_API_CLOSE_JOIN_H
#include "driver-api-close-owner.h"
#include "mbss-close-recovery-owner.h"
struct wr_iot_driver_close_join_receipt {
 const void *device;
 unsigned long generation,open_token,epoch,serial;
};
static inline int wr_iot_driver_close_join_claim(
 struct wr_iot_driver_close_owner *close,
 const struct wr_iot_mbss_recovery_owner *recovery,
 const struct wr_iot_interface_ref *record,int work_joined,
 struct wr_iot_driver_close_join_receipt *receipt)
{
 if(!close||!recovery||!record||!receipt||!work_joined||!close->active||
    !close->consumed||close->task||!close->module_held||close->netdev_held||
    close->synchronous_put_pending||close->synchronous_netdev_returned||
    !close->recovery_netdev_transferred||close->recovery_join_pending||
    close->recovery_netdev_returned||!recovery->completed||
    !recovery->deferred_owners||!recovery->close_ticket_valid||
    (recovery->phase!=WR_MBSS_OWNER_RUNNING&&recovery->phase!=WR_MBSS_OWNER_STOPPING)||
    close->ticket.operation!=WR_RADIO_BSS_CLOSE||close->ticket.reset_kind||
    recovery->device!=close->device||recovery->generation!=close->generation||
    recovery->open_token!=close->open_token||recovery->close_serial!=close->ticket.serial||
    recovery->close_ticket.serial!=close->ticket.serial||
    recovery->close_ticket.epoch!=close->ticket.epoch||
    recovery->close_ticket.operation!=close->ticket.operation||recovery->close_ticket.reset_kind||
    recovery->close_ticket.prior_phase!=close->ticket.prior_phase||
    recovery->close_ticket.prior_ready!=close->ticket.prior_ready||
    record->device!=close->device||record->generation!=close->generation||
    record->last_token!=close->open_token||!record->published||record->removing||
    record->removal_stage||record->family!=WR_REF_FAMILY_MBSS||
    record->phase!=WR_REF_IDLE||record->close_stage!=4||record->close_running||
    record->close_uncertain_reason||record->close_serial!=close->ticket.serial||
    !wr_iot_mbss_recovery_ticket_recorded(record,&close->ticket))return 0;
 receipt->device=close->device;receipt->generation=close->generation;
 receipt->open_token=close->open_token;receipt->epoch=close->ticket.epoch;
 receipt->serial=close->ticket.serial;close->recovery_join_pending=1;
 return 1;
}
/* Caller invokes only after the claimed dev_put actually returned, while
 * still holding the exclusive reaper lease and adapter/API lifetime fence. */
static inline int wr_iot_driver_close_join_returned(
 struct wr_iot_driver_close_owner *close,
 const struct wr_iot_driver_close_join_receipt *receipt)
{
 if(!close||!receipt||!close->active||!close->consumed||close->task||
    close->synchronous_put_pending||close->synchronous_netdev_returned||
    !close->module_held||close->netdev_held||!close->recovery_netdev_transferred||
    !close->recovery_join_pending||close->recovery_netdev_returned||
    close->device!=receipt->device||close->generation!=receipt->generation||
    close->open_token!=receipt->open_token||close->ticket.epoch!=receipt->epoch||
    close->ticket.serial!=receipt->serial)return 0;
 close->recovery_netdev_returned=1;close->recovery_join_pending=0;return 1;
}
#endif
