#ifndef WR_IOT_PHYSICAL_REBIND_OPEN_H
#define WR_IOT_PHYSICAL_REBIND_OPEN_H
#include "physical-rebind-probe.h"
#include "driver-api-owner.h"
/* Caller owns transition lock and real task/PID/netdev/adapter lifetime. Consume
 * handoff and reserve existing OPEN owner without unlocking in between. This
 * does not perform dev_open, credential comparison, beacon or RF acceptance.
 * A failed reserve keeps spent identity: it cannot become a replay permission. */
static inline int wr_iot_physical_rebind_open_reserve(
 struct wr_iot_physical_rebind_probe *probe,
 const struct wr_iot_physical_stop_terminal *terminal,const struct pid *issuer,
 const struct wr_iot_physical_stop_request *physical_request,
 const struct wr_iot_main_recovery_owner *main_owner,struct wr_iot_driver_owner *open_owner,
 struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,unsigned count,
 const void *main_dev,const void *iot_dev,unsigned vendor_count,const void *task,
 const struct wr_iot_driver_open_request *request,unsigned control_users,int blocked)
{
 unsigned i,difference=0,prior_open=0,prior_refusal=0,prior_uncertain=0;
 if(!open_owner||!request||!task||open_owner->active||open_owner->poisoned||
    control_users||blocked||!open_owner->query_valid||
    request->adapter_epoch!=open_owner->query_epoch||
    request->device_generation!=open_owner->query_generation||!radio||
    request->adapter_epoch!=radio->epoch||!physical_request||
    request->device_generation!=physical_request->generation)return 0;
 for(i=0;i<16;i++)difference|=request->request_id[i]^open_owner->query_id[i];
 if(difference)return 0;
 for(i=0;i<16;i++){
  prior_open|=request->request_id[i]^open_owner->receipt.request_id[i];
  prior_refusal|=request->request_id[i]^open_owner->refusal.request_id[i];
  prior_uncertain|=request->request_id[i]^open_owner->uncertain_request_id[i];
 }
 if(!prior_open||!prior_refusal||!prior_uncertain)return 0;
 if(!wr_iot_physical_rebind_claim(probe,terminal,issuer,physical_request,main_owner,
    radio,slots,count,main_dev,iot_dev,vendor_count,request->request_id))return 0;
 return wr_iot_driver_owner_reserve(open_owner,radio,slots,count,main_dev,iot_dev,
  vendor_count,task,request,control_users,blocked);
}
#endif
