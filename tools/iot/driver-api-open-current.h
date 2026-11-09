/* Locked observation only. Caller pins lifetimes and holds RTNL/transition
 * lock. Do not use the returned token as a lease after unlocking. */
#ifndef WR_IOT_DRIVER_API_OPEN_CURRENT_H
#define WR_IOT_DRIVER_API_OPEN_CURRENT_H
#include "driver-api-close-admission.h"
#include "driver-api-open-current-wire.h"
static inline int wr_iot_driver_open_current_observe(
 const struct wr_iot_driver_owner *owner,const unsigned char *nonce,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned int vendor_count,unsigned int users,int blocked,int probe,
 struct wr_iot_driver_open_current_result *out)
{
 unsigned long epoch,generation,token;
 if(!out)return 0;
 out->adapter_epoch=out->device_generation=out->open_token=0;
 /* Configuration receipt alone remains sufficient for CLOSE admission,
  * but cannot advertise first-publication completion to the RC observer. */
 if(!owner||owner->receipt.first_beacon_confirmed!=1)return 0;
 epoch=owner->receipt.epoch;generation=owner->receipt.generation;
 token=owner->receipt.open_token;
 if(!wr_iot_driver_close_admissible(owner,nonce,radio,slots,count,main_dev,
    iot_dev,epoch,generation,token,vendor_count,users,blocked,probe))return 0;
 out->adapter_epoch=epoch;out->device_generation=generation;out->open_token=token;
 return 1;
}
#endif
