/* Locked identity check for future CLOSE progress orchestration only.
 * Does not replay dev_close, allocate tickets, release refs or grant RF safety.
 * Compare wire 64-bit identities before narrowing on MIPS32. */
#ifndef WR_IOT_DRIVER_API_CLOSE_PROGRESS_MATCH_H
#define WR_IOT_DRIVER_API_CLOSE_PROGRESS_MATCH_H
#include "driver-api-close-owner.h"
#include "driver-api-close-wire.h"
static inline int wr_iot_driver_close_progress_matches(
 const struct wr_iot_driver_close_owner *close,
 const struct wr_iot_driver_owner *open,const void *device,
 const struct wr_iot_driver_close_request *request)
{
 if(!close||!open||!device||!request||!close->active||close->device!=device||
    close->task||!close->ticket.epoch||!close->generation||!close->open_token||
    close->ticket.operation!=WR_RADIO_BSS_CLOSE||close->ticket.reset_kind||
    request->adapter_epoch!=(unsigned long long)close->ticket.epoch||
    request->device_generation!=(unsigned long long)close->generation||
    request->open_token!=(unsigned long long)close->open_token)return 0;
 return wr_iot_driver_open_receipt_matches(open,request->open_request_id,device,
  close->ticket.epoch,close->generation,close->open_token);
}
#endif
