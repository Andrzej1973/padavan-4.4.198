/* Locked preflight for future dedicated retirement-thread admission.
 * Caller owns adapter/registration lifetime and supplies actual joined-work
 * observation. This is not a lease after unlock, resource release, RF receipt,
 * permission to reopen or isolation-removal authority. */
#ifndef WR_IOT_DRIVER_API_CLOSE_RETIREMENT_H
#define WR_IOT_DRIVER_API_CLOSE_RETIREMENT_H
#include "driver-api-close-owner.h"
#include "mbss-close-receipt.h"
#include "mbss-recovery-storage.h"
#include "mbss-poll-lifetime.h"
#include "mbss-reaper-gate.h"
static inline int wr_iot_driver_close_retirement_ready(
 const struct wr_iot_driver_close_owner *close,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_dev,unsigned int vendor_count,
 const struct wr_iot_mbss_recovery_owner *recovery,unsigned int recovery_count,
 const struct wr_iot_mbss_poll_lifetime *poll,
 const struct wr_iot_mbss_reaper_gate *reaper,int work_idle)
{
 struct wr_iot_interface_ref *main,*record;
 if(!close||!radio||radio->epoch!=close->ticket.epoch||!close->active||!close->consumed||close->task||
    !close->module_held||close->netdev_held||!close->recovery_netdev_transferred||
    close->recovery_join_pending||!close->recovery_netdev_returned||
    close->ticket.operation!=WR_RADIO_BSS_CLOSE||close->ticket.reset_kind||
    !poll||poll->pending||poll->running||poll->unjoined||poll->joining||
    !work_idle||!wr_iot_mbss_reaper_idle(reaper)||
    !wr_iot_mbss_recovery_storage_idle(recovery,recovery_count)||
    !wr_iot_mbss_closed_reference(radio,slots,count,main_dev,close->device,
      close->generation,close->open_token,close->ticket.serial,vendor_count))return 0;
 record=wr_iot_registry_find(slots,count,close->device,close->generation);
 if(!record||record->close_epoch!=close->ticket.epoch||
    record->close_prior_phase!=(int)close->ticket.prior_phase||
    record->close_prior_ready!=close->ticket.prior_ready)return 0;
 main=wr_iot_registry_find_owned(slots,count,main_dev);
 return main&&main->last_token&&!main->removal_stage&&!main->close_running&&
        !main->close_uncertain_reason;
}
#endif
