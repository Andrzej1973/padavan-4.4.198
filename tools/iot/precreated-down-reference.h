/* Read-only never-opened ra2 after independently completed Main close.
 * Caller pins adapter/netdev lifetime, holds transition lock and separately
 * verifies peer/control/descriptor owners. Not RF/DMA/IRQ retirement permission. */
#ifndef WR_IOT_PRECREATED_DOWN_REFERENCE_H
#define WR_IOT_PRECREATED_DOWN_REFERENCE_H
#include "main-open-recovery-owner.h"
static inline int wr_iot_precreated_down_reference(
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned long generation,unsigned int vendor_count)
{
 struct wr_iot_interface_ref *main,*iot;unsigned int i;
 if(!owner||!radio||!slots||!main_dev||!iot_dev||main_dev==iot_dev||
    !generation||vendor_count||owner->last_release.device!=main_dev||
    !owner->last_release.generation||owner->device||owner->generation||
    owner->open_token||owner->close_serial||owner->close_ticket_valid||
    owner->schedule_recorded||radio->exhausted)return 0;
 main=wr_iot_registry_find(slots,count,main_dev,owner->last_release.generation);
 iot=wr_iot_registry_find(slots,count,iot_dev,generation);
 if(!main||!iot||!wr_iot_main_recovery_release_current(owner,radio,main,vendor_count)||
    !iot->published||iot->family!=WR_REF_FAMILY_MBSS||iot->phase!=WR_REF_IDLE||
    iot->last_token||iot->open_unmutated||iot->close_serial||iot->close_epoch||
    iot->close_stage||iot->close_running||iot->close_uncertain_reason||
    iot->close_vendor_count||iot->close_verified_stage||iot->close_prior_phase||
    iot->close_prior_ready)return 0;
 for(i=0;i<count;i++)if(slots[i].device&&
    (slots[i].phase!=WR_REF_IDLE||!slots[i].published||slots[i].removing||
     slots[i].removal_stage||slots[i].close_running||slots[i].close_uncertain_reason))return 0;
 return wr_iot_registry_count_matches(slots,count,0);
}
#endif
