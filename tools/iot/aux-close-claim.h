/* Isolated non-last auxiliary close admission; caller holds adapter lock and
 * pins adapter/netdev lifetime. No vendor, HNAT or queue mutation occurs here.
 * Last-reference physical close needs a separate recovery owner. */
#ifndef WR_IOT_AUX_CLOSE_CLAIM_H
#define WR_IOT_AUX_CLOSE_CLAIM_H
#include "interface-registry.h"
#include "radio-transition.h"

static inline int wr_iot_aux_close_reserve(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,enum wr_iot_ref_family family,unsigned int vendor_count,
 struct wr_iot_radio_ticket *ticket,unsigned long *generation){
 struct wr_iot_interface_ref *record;
 if(!radio||!slots||!device||!ticket||!generation||vendor_count<=1||
    (family!=WR_REF_FAMILY_WDS&&family!=WR_REF_FAMILY_APCLI&&
     family!=WR_REF_FAMILY_MONITOR))return 0;
 record=wr_iot_registry_find_owned(slots,count,device);
 if(!record||record->family!=family||!record->last_token||
    !wr_iot_registry_count_matches(slots,count,vendor_count))return 0;
 if(!wr_iot_radio_begin(radio,radio->epoch,WR_RADIO_AUX_CLOSE,ticket))return 0;
 if(!wr_iot_ref_begin_close(record,device,record->generation,
                            record->last_token)){
  wr_iot_radio_abort_aux_close_unmutated(radio,ticket);
  return 0;
 }
 record->close_serial=ticket->serial;
 record->close_epoch=ticket->epoch;
 record->close_vendor_count=vendor_count;
 record->close_prior_phase=(int)ticket->prior_phase;
 record->close_prior_ready=ticket->prior_ready;
 record->close_stage=0;
 *generation=record->generation;
 return 1;
}
/* Resume only a failed DOWN with no vendor-count mutation. The original
 * ndo_stop stack is gone, so reconstruct the SAME ticket from its recorded
 * identity; never begin another AUX_CLOSE or replay queue/HNAT effects.
 * Caller holds the adapter lock and pins adapter/netdev lifetime. */
static inline int wr_iot_aux_close_retry_unmutated_down(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,enum wr_iot_ref_family family,unsigned int vendor_count,
 struct wr_iot_radio_ticket *ticket,unsigned long *generation){
 struct wr_iot_interface_ref *record;
 unsigned int i;
 if(!radio||!slots||!device||!ticket||!generation||
    radio->busy!=WR_RADIO_AUX_CLOSE||radio->virtual_down_stage||
    radio->reset_pending||radio->retiring||radio->pm_suspending||
    radio->pm_suspended||radio->phase!=WR_RADIO_READY)return 0;
 /* A closing record is not OWNED; find it by exact device and family. */
 record=0;
 for(i=0;i<count;i++)if(slots[i].device==device&&
    slots[i].family==family&&slots[i].phase==WR_REF_CLOSING){
  if(record)return 0; /* duplicate registration is ambiguous */
  record=&slots[i];
 }
 if(!record||record->phase!=WR_REF_CLOSING||record->family!=family||
    !record->published||!record->generation||!record->last_token||
    record->close_stage!=1||record->close_serial!=radio->serial||
    record->close_epoch!=radio->epoch||
    record->close_vendor_count!=vendor_count||vendor_count<=1)return 0;
 ticket->serial=record->close_serial;ticket->epoch=record->close_epoch;
 ticket->operation=WR_RADIO_AUX_CLOSE;ticket->reset_kind=0;
 ticket->prior_phase=(enum wr_iot_radio_phase)record->close_prior_phase;
 ticket->prior_ready=record->close_prior_ready;
 *generation=record->generation;
 record->close_stage=3; /* one continuation owns the retained ticket */
 return 1;
}
/* Release a failed retry claim only when DOWN made no count mutation. */
static inline int wr_iot_aux_close_retry_release(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,unsigned long generation,
 const struct wr_iot_radio_ticket *ticket){
 struct wr_iot_interface_ref *record;
 if(!radio||!ticket||ticket->operation!=WR_RADIO_AUX_CLOSE||
    radio->virtual_down_stage||
    radio->busy!=WR_RADIO_AUX_CLOSE||radio->serial!=ticket->serial)return 0;
 record=wr_iot_registry_find(slots,count,device,generation);
 if(!record||record->phase!=WR_REF_CLOSING||
    record->close_stage!=3||record->close_serial!=ticket->serial||
    record->close_epoch!=ticket->epoch)return 0;
 record->close_stage=1;return 1;
}
/* Finish a DOWN whose vendor count is already decremented. Never call DOWN
 * again. Caller holds the common adapter lock. A failed radio completion
 * leaves stage 4 for a retained recovery owner; no module pin is released. */
static inline int wr_iot_aux_close_finalize_after_down(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,unsigned long generation,
 const struct wr_iot_radio_ticket *ticket,unsigned int expected_stage,
 unsigned int vendor_count){
 struct wr_iot_interface_ref *record;
 if(!radio||!ticket||ticket->operation!=WR_RADIO_AUX_CLOSE||
    radio->busy!=WR_RADIO_AUX_CLOSE||radio->serial!=ticket->serial||
    radio->virtual_down_stage!=2||
    (expected_stage!=1&&expected_stage!=3&&expected_stage!=5))return 0;
 record=wr_iot_registry_find(slots,count,device,generation);
 if(!record||record->phase!=WR_REF_CLOSING||
    record->close_stage!=expected_stage||
    record->close_serial!=ticket->serial||
    record->close_epoch!=ticket->epoch||!record->last_token||
    record->close_vendor_count<=1||
    vendor_count!=record->close_vendor_count-1||
    !wr_iot_ref_matches(record,device,generation,record->last_token))return 0;
 if(!wr_iot_radio_finish(radio,ticket,1)){
  record->close_stage=4;return 0;
 }
 /* The locked preflight above establishes every ref_consume precondition. */
 if(!wr_iot_ref_consume(record,device,generation,record->last_token))return 0;
 record->close_stage=2;return 1;
}
/* Only a stage-4 retained owner may claim post-DOWN reconciliation. It
 * reconstructs the original ticket and advances to stage 5 atomically. */
static inline int wr_iot_aux_close_claim_after_down(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,enum wr_iot_ref_family family,unsigned int vendor_count,
 struct wr_iot_radio_ticket *ticket,unsigned long *generation){
 struct wr_iot_interface_ref *record;
 unsigned int i;
 if(!radio||!slots||!device||!ticket||!generation||
    radio->busy!=WR_RADIO_AUX_CLOSE||radio->virtual_down_stage!=2)return 0;
 record=0;
 for(i=0;i<count;i++)if(slots[i].device==device&&
    slots[i].phase==WR_REF_CLOSING){
  if(record)return 0;
  record=&slots[i];
 }
 if(!record||record->family!=family||record->close_stage!=4||
    record->close_serial!=radio->serial||!record->close_epoch||
    record->close_vendor_count<=1||
    vendor_count!=record->close_vendor_count-1)return 0;
 ticket->serial=record->close_serial;ticket->epoch=record->close_epoch;
 ticket->operation=WR_RADIO_AUX_CLOSE;ticket->reset_kind=0;
 ticket->prior_phase=(enum wr_iot_radio_phase)record->close_prior_phase;
 ticket->prior_ready=record->close_prior_ready;
 *generation=record->generation;
 record->close_stage=5;return 1;
}
#endif
