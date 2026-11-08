/* Locked preflight for the future RC close entry. This is admission only,
 * not a ticket reservation, dev_close result, RF receipt or rollback permit.
 * Caller pins lifetimes and holds RTNL plus the adapter transition lock.
 * The eventual executor must reserve and transfer ONE BSS_CLOSE ticket under
 * that same lock before releasing it; never use this boolean after unlock. */
#ifndef WR_IOT_DRIVER_API_CLOSE_ADMISSION_H
#define WR_IOT_DRIVER_API_CLOSE_ADMISSION_H
#include "driver-api-owner.h"
static inline int wr_iot_driver_close_admissible(
 const struct wr_iot_driver_owner *owner,
 const unsigned char *nonce,const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_dev,const void *iot_dev,unsigned long epoch,
 unsigned long generation,unsigned long open_token,unsigned int vendor_count,
 unsigned int control_users,int control_blocked,int probe_active)
{
 struct wr_iot_interface_ref *main_ref,*iot_ref;
 if(!radio||!slots||!main_dev||!iot_dev||main_dev==iot_dev||
    !epoch||!generation||!open_token||vendor_count<=1||control_users||
    control_blocked||probe_active||radio->epoch!=epoch||radio->busy||
    radio->phase!=WR_RADIO_READY||!radio->main_ready||radio->main_inhibited||
    radio->reset_pending||radio->retiring||radio->exhausted||
    radio->pm_suspending||radio->pm_suspended||
    !wr_iot_driver_open_receipt_matches(owner,nonce,iot_dev,epoch,generation,open_token))return 0;
 main_ref=wr_iot_registry_find_owned(slots,count,main_dev);
 iot_ref=wr_iot_registry_find_owned(slots,count,iot_dev);
 if(!main_ref||main_ref->family!=WR_REF_FAMILY_MAIN||main_ref->removing||
    main_ref->removal_stage||!main_ref->last_token||main_ref->close_running||
    main_ref->close_uncertain_reason||
    !iot_ref||iot_ref->family!=WR_REF_FAMILY_MBSS||iot_ref->removing||iot_ref->removal_stage||
    iot_ref->generation!=generation||iot_ref->last_token!=open_token||
    iot_ref->close_running||iot_ref->close_uncertain_reason)return 0;
 return wr_iot_registry_count_matches(slots,count,vendor_count);
}
#endif
