/* Initial never-opened registration only. Caller holds transition lock and
 * pins adapter/netdev under RTNL. This is software admission, not beacon,
 * DMA/TxS, loaded-key or RF proof. A previously attempted OPEN needs its own
 * refusal/CLOSE recovery receipt and cannot be relabelled as initial idle. */
#ifndef WR_IOT_PRECREATED_IDLE_REFERENCE_H
#define WR_IOT_PRECREATED_IDLE_REFERENCE_H
#include "radio-transition-api.h"
#include "interface-registry.h"
static inline int wr_iot_precreated_idle_reference(
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned long generation,unsigned int vendor_count)
{
 struct wr_iot_interface_ref *main,*iot;
 if(!radio||!main_dev||!iot_dev||main_dev==iot_dev||!generation||!vendor_count||
    !radio->epoch||radio->busy||radio->phase!=WR_RADIO_READY||!radio->main_ready||
    radio->main_inhibited||radio->reset_pending||radio->retiring||radio->exhausted||
    radio->pm_suspending||radio->pm_suspended)return 0;
 main=wr_iot_registry_find_owned(slots,count,main_dev);
 iot=wr_iot_registry_find(slots,count,iot_dev,generation);
 if(!main||main->family!=WR_REF_FAMILY_MAIN||main->removing||main->removal_stage||
    !main->last_token||main->close_running||main->close_uncertain_reason||
    !iot||iot->family!=WR_REF_FAMILY_MBSS||!iot->published||iot->removing||
    iot->removal_stage||iot->phase!=WR_REF_IDLE||iot->last_token||
    iot->open_unmutated||iot->close_serial||iot->close_epoch||iot->close_stage||
    iot->close_running||iot->close_uncertain_reason||iot->close_vendor_count||
    iot->close_verified_stage||iot->close_prior_phase||iot->close_prior_ready)return 0;
 return wr_iot_registry_count_matches(slots,count,vendor_count);
}
#endif
