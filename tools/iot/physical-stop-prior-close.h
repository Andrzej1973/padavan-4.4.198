/* Read-only prior IoT CLOSE admission under existing transition/registry lock.
 * Reuses the actual release verifier on a local copy; never reactivates owner.
 * This proves prior BSS configuration/reference state, not physical teardown. */
#ifndef WR_IOT_PHYSICAL_STOP_PRIOR_CLOSE_H
#define WR_IOT_PHYSICAL_STOP_PRIOR_CLOSE_H
#include "physical-stop-wire.h"
#include "driver-api-close-release.h"
static inline int wr_iot_physical_stop_prior_close(
 const struct wr_iot_physical_stop_request *request,
 const struct wr_iot_driver_close_owner *close,
 const struct wr_iot_driver_owner *open,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_dev,const void *iot_dev,unsigned int vendor_count,
 const struct wr_iot_mbss_closed_probe *probe,
 const struct wr_iot_beacon_producer_gate *producer,unsigned long producer_generation)
{
 struct wr_iot_driver_close_owner observed;
 struct wr_iot_driver_close_request retained;unsigned i;
 if(!wr_iot_physical_stop_request_valid(request)||request->action!=WR_STOP_ARM||
    !close||!open||close->active||open->active||open->poisoned||
    !open->receipt.valid||open->receipt.device!=iot_dev||
    request->epoch!=open->receipt.epoch||request->epoch!=close->ticket.epoch||
    request->generation!=open->receipt.generation||request->generation!=close->generation||
    request->open_token!=open->receipt.open_token||request->open_token!=close->open_token||
    request->closed_serial!=close->ticket.serial)return 0;
 for(i=0;i<16;i++)retained.open_request_id[i]=open->receipt.request_id[i];
 retained.adapter_epoch=request->epoch;retained.device_generation=request->generation;
 retained.open_token=request->open_token;observed=*close;
 return wr_iot_driver_close_release_reference(&observed,open,&retained,radio,
  slots,count,main_dev,iot_dev,vendor_count,probe,producer,producer_generation);
}
#endif
