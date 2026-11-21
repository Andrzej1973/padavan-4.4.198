/* Reference bookkeeping preflight for the future CLOSED query. Caller holds
 * transition lock and pins adapter/netdev lifetime. This is NOT RF silence,
 * beacon producer/DMA/TxS drain or a permission to release network isolation. */
#ifndef WR_IOT_MBSS_CLOSE_RECEIPT_H
#define WR_IOT_MBSS_CLOSE_RECEIPT_H
#include "interface-registry.h"
#include "radio-transition.h"
static inline int wr_iot_mbss_closed_record_current(
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned long generation,unsigned long open_token,unsigned long close_serial,
 unsigned int vendor_count)
{
 struct wr_iot_interface_ref *main_ref,*record;
 if(!radio||!main_dev||!iot_dev||main_dev==iot_dev||!generation||!open_token||
    !close_serial||!vendor_count||radio->phase!=WR_RADIO_READY||!radio->main_ready||
    radio->main_inhibited||radio->reset_pending||radio->retiring||
    radio->pm_suspending||radio->pm_suspended||radio->exhausted)return 0;
 main_ref=wr_iot_registry_find_owned(slots,count,main_dev);
 record=wr_iot_registry_find(slots,count,iot_dev,generation);
 if(!main_ref||main_ref->family!=WR_REF_FAMILY_MAIN||main_ref->removing||
    main_ref->removal_stage||!main_ref->last_token||main_ref->close_running||
    main_ref->close_uncertain_reason||
    !record||record->family!=WR_REF_FAMILY_MBSS||!record->published||record->removing||
    record->removal_stage||
    record->phase!=WR_REF_IDLE||record->open_unmutated||
    record->last_token!=open_token||record->close_serial!=close_serial||
    record->close_stage!=4U||record->close_running||record->close_uncertain_reason||
    record->close_epoch!=radio->epoch||record->close_vendor_count<=1)return 0;
 return wr_iot_registry_count_matches(slots,count,vendor_count);
}
/* Idle preflight; an already-owned observation uses the record helper above
 * only after validating its exact BSS_OBSERVE ticket. */
static inline int wr_iot_mbss_closed_reference(
 const struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *slots,
 unsigned int count,const void *main_dev,const void *iot_dev,
 unsigned long generation,unsigned long open_token,unsigned long close_serial,
 unsigned int vendor_count){
 return radio&&!radio->busy&&wr_iot_mbss_closed_record_current(radio,slots,count,
  main_dev,iot_dev,generation,open_token,close_serial,vendor_count);
}
#endif
