/* Compile-only no-host beacon mode. Caller owns RTNL, transition_lock and
 * adapter/netdev lifetime, and must have established the immutable no-host
 * mode plus a successful current CLOSED configuration probe. This helper
 * consumes only software ownership. It never releases packets or isolation.
 * Production integration is pending and must supply those actual conditions. */
#ifndef WR_IOT_DRIVER_API_CLOSE_RELEASE_H
#define WR_IOT_DRIVER_API_CLOSE_RELEASE_H
#include "driver-api-close-progress-match.h"
#include "mbss-closed-probe.h"
#include "beacon-producer-gate.h"
static inline int wr_iot_driver_close_release_reference(
 struct wr_iot_driver_close_owner *close,
 const struct wr_iot_driver_owner *open,
 const struct wr_iot_driver_close_request *request,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_dev,const void *device,unsigned int vendor_count,
 const struct wr_iot_mbss_closed_probe *probe,
 const struct wr_iot_beacon_producer_gate *producer,unsigned long producer_generation)
{
 struct wr_iot_driver_close_owner retained;
 struct wr_iot_interface_ref *record;
 if(!close||!radio||!probe||!producer||!producer_generation||
    !close->retirement_module_transferred||!close->consumed||
    probe->active||probe->main_device!=main_dev||probe->iot_device!=device||
    probe->generation!=close->generation||probe->open_token!=close->open_token||
    probe->close_serial!=close->ticket.serial||
    probe->ticket.operation!=WR_RADIO_BSS_OBSERVE||probe->ticket.reset_kind||
    probe->ticket.epoch!=close->ticket.epoch||radio->epoch!=close->ticket.epoch||
    !probe->ticket.serial||radio->retired_serial!=probe->ticket.serial||
    !wr_iot_beacon_gate_drained(producer,producer_generation))return 0;
 /* Treat a previously released owner as retained only for validation. This
  * makes a lost successful reply repeatable until a new OPEN replaces the
  * original receipt or registry record. Never reactivate the stored owner. */
 retained=*close;
 retained.active=1;
 if(wr_iot_driver_close_blocks_adapter_retirement(&retained)||
    !wr_iot_driver_close_progress_matches(&retained,open,device,request)||
    !wr_iot_mbss_closed_reference(radio,slots,count,main_dev,device,
      close->generation,close->open_token,close->ticket.serial,vendor_count))return 0;
 record=wr_iot_registry_find(slots,count,device,close->generation);
 if(!record||record->close_prior_phase!=(int)close->ticket.prior_phase||
    record->close_prior_ready!=close->ticket.prior_ready)return 0;
 close->active=0;
 return 1;
}
#endif
