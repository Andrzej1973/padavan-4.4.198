/* Caller holds transition_lock and requires the existing live timer/adapter
 * lifecycle. This counter does not independently pin or retire that object.
 * Compare netdev pointers only. Registry/receipt validity supplies identity;
 * no borrowed netdev is dereferenced. An admitted callback retains the existing
 * control_users fence until it returns, excluding CLOSE/new transition owners.
 * This is a host software-operation fence, not an RF/DMA completion receipt. */
#ifndef WR_IOT_RA2_REKEY_ADMISSION_H
#define WR_IOT_RA2_REKEY_ADMISSION_H
#include "driver-api-owner.h"
static inline int wr_iot_ra2_rekey_admit(
 const struct wr_iot_driver_owner *owner,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_dev,const void *iot_dev,unsigned int vendor_count,
 unsigned int *users,unsigned int *poisoned,int blocked)
{
 struct wr_iot_interface_ref *main_ref,*iot_ref;
 unsigned int i,nonce=0;
 if(!owner||!radio||!slots||!users||!poisoned||*poisoned||blocked||
    !main_dev||!iot_dev||main_dev==iot_dev||vendor_count<2||
    !radio->epoch||radio->phase!=WR_RADIO_READY||!radio->main_ready||radio->main_inhibited||
    radio->busy||radio->reset_pending||radio->retiring||radio->exhausted||
    radio->pm_suspending||radio->pm_suspended||
    !owner->receipt.first_beacon_confirmed)return 0;
 for(i=0;i<16;i++)nonce|=owner->receipt.request_id[i];
 if(!nonce)return 0;
 main_ref=wr_iot_registry_find_owned(slots,count,main_dev);
 iot_ref=wr_iot_registry_find_owned(slots,count,iot_dev);
 if(!main_ref||main_ref->family!=WR_REF_FAMILY_MAIN||main_ref->removing||
    main_ref->removal_stage||!main_ref->last_token||main_ref->close_running||
    main_ref->close_uncertain_reason||
    !iot_ref||iot_ref->family!=WR_REF_FAMILY_MBSS||iot_ref->removing||
    iot_ref->removal_stage||!iot_ref->last_token||iot_ref->close_running||
    iot_ref->close_uncertain_reason||
    !wr_iot_registry_count_matches(slots,count,vendor_count)||
    !wr_iot_driver_open_receipt_matches(owner,owner->receipt.request_id,iot_dev,
     radio->epoch,iot_ref->generation,iot_ref->last_token))return 0;
 /* Other admitted control actors are allowed. This is a counted lifetime/
  * transition fence, not an exclusive global periodic-worker lock. */
 if(*users==~0U){*poisoned=1;return 0;}
 ++*users;return 1;
}
#endif
