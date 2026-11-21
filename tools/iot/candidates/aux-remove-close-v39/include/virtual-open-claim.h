/* Isolated shared-dispatcher admission check; not installed in the driver.
 * Caller holds the adapter transition lock and pins adapter/netdev lifetime.
 * The family wrapper owns one ticket from preflight through vendor mutation.
 * This check consumes no reference and never begins a second ticket. */
#ifndef WR_IOT_VIRTUAL_OPEN_CLAIM_H
#define WR_IOT_VIRTUAL_OPEN_CLAIM_H
#include "interface-registry.h"
#include "radio-transition.h"

struct wr_iot_virtual_open_claim {
 const void *device;
 unsigned long generation,serial,epoch;
 int operation;
};

/* Main ra0 admission is one transaction under the adapter transition lock.
 * The caller has already pinned the exact adapter main netdevice. On success
 * it owns both ticket and RESERVED record before invoking AP_MAIN_OPEN. */
static inline int wr_iot_main_open_reserve(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_device,unsigned int vendor_count,
 struct wr_iot_radio_ticket *ticket,unsigned long *generation){
 struct wr_iot_interface_ref *record;
 int operation;
 if(!radio||!slots||!main_device||!ticket||!generation||
    vendor_count==~0U)return 0;
 record=wr_iot_registry_find_openable(slots,count,main_device);
 if(!record)return 0;
 operation=vendor_count?WR_RADIO_MAIN_OPEN:WR_RADIO_START;
 if(!wr_iot_radio_begin(radio,radio->epoch,operation,ticket))return 0;
 if(!wr_iot_ref_reserve(record,main_device,record->generation,
                        ticket->serial)){
  wr_iot_radio_abort_main_open_unmutated(radio,ticket);
  return 0;
 }
 *generation=record->generation;
 return 1;
}

/* AP-client/WDS/monitor share the vendor count with main/MBSS. Reserve the
 * AUX ticket and exact published netdev record under the same adapter lock
 * before their wrapper invokes vendor OPEN or VIRTUAL_IF_UP. A zero count
 * claims the physical start; a nonzero count claims only an auxiliary open.
 * No HNAT, queue, vendor state or count is changed here. */
static inline int wr_iot_aux_open_reserve(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,enum wr_iot_ref_family family,unsigned int vendor_count,
 struct wr_iot_radio_ticket *ticket,unsigned long *generation){
 struct wr_iot_interface_ref *record;
 if(!radio||!slots||!device||!ticket||!generation||
    (family!=WR_REF_FAMILY_APCLI&&family!=WR_REF_FAMILY_WDS&&
     family!=WR_REF_FAMILY_MONITOR)||
    vendor_count==~0U)return 0;
 record=wr_iot_registry_find_openable(slots,count,device);
 if(!record||record->family!=family)return 0;
 if(!wr_iot_radio_begin_aux_open(radio,vendor_count,ticket))return 0;
 if(!wr_iot_ref_reserve(record,device,record->generation,ticket->serial)){
  wr_iot_radio_abort_aux_open_unmutated(radio,ticket);
  return 0;
 }
 *generation=record->generation;
 return 1;
}

static inline int wr_iot_virtual_open_claim_matches(
 const struct wr_iot_virtual_open_claim *claim,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count){
 struct wr_iot_interface_ref *record;
 if(!claim||!radio||!claim->device||!claim->generation||
    !claim->serial||!claim->epoch||
    (claim->operation!=WR_RADIO_BSS_OPEN&&
     claim->operation!=WR_RADIO_AUX_OPEN&&
     claim->operation!=WR_RADIO_AUX_START&&
     claim->operation!=WR_RADIO_START&&
     claim->operation!=WR_RADIO_MAIN_OPEN))return 0;
 if(radio->busy!=claim->operation||radio->serial!=claim->serial||
    radio->virtual_up_stage||
    radio->epoch!=claim->epoch||radio->reset_pending||radio->retiring||
    radio->pm_suspending||radio->pm_suspended||radio->exhausted)return 0;
 if(claim->operation==WR_RADIO_BSS_OPEN){
  if(radio->phase!=WR_RADIO_READY||!radio->main_ready||
     radio->main_inhibited)return 0;
 }else if(claim->operation==WR_RADIO_AUX_OPEN){
  if(radio->phase!=WR_RADIO_READY)return 0;
 }else if(claim->operation==WR_RADIO_MAIN_OPEN){
  if(radio->phase!=WR_RADIO_READY&&radio->phase!=WR_RADIO_UNVERIFIED)return 0;
 }else if(radio->phase!=WR_RADIO_DOWN)return 0;
 record=wr_iot_registry_find(slots,count,claim->device,claim->generation);
 return record&&record->published&&!record->removing&&
   record->phase==WR_REF_RESERVED&&record->last_token==claim->serial;
}
/* A main claim must additionally name the adapter's physical netdevice.
 * The dispatcher must still verify the matching vendor count and perform
 * first-open hardware work outside the short transition lock. */
static inline int wr_iot_virtual_main_open_claim_matches(
 const struct wr_iot_virtual_open_claim *claim,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_device,unsigned int vendor_count){
 if(!claim||!main_device||claim->device!=main_device||
    (claim->operation!=WR_RADIO_START&&claim->operation!=WR_RADIO_MAIN_OPEN)||
    (claim->operation==WR_RADIO_START&&vendor_count!=0)||
    (claim->operation==WR_RADIO_MAIN_OPEN&&vendor_count==0))return 0;
 return wr_iot_virtual_open_claim_matches(claim,radio,slots,count);
}
/* Recheck an auxiliary claim immediately before the shared dispatcher changes
 * VirtualIfCnt. The registered family is authoritative, not the caller's
 * requested operation; main and MBSS records may never use this path. */
static inline int wr_iot_virtual_aux_open_claim_matches(
 const struct wr_iot_virtual_open_claim *claim,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *main_device,unsigned int vendor_count){
 struct wr_iot_interface_ref *record;
 if(!claim||!main_device||claim->device==main_device||
    (claim->operation!=WR_RADIO_AUX_START&&
     claim->operation!=WR_RADIO_AUX_OPEN)||
    (claim->operation==WR_RADIO_AUX_START&&vendor_count!=0)||
    (claim->operation==WR_RADIO_AUX_OPEN&&
     (vendor_count==0||vendor_count==~0U)))return 0;
 record=wr_iot_registry_find(slots,count,claim->device,claim->generation);
 if(!record||(record->family!=WR_REF_FAMILY_APCLI&&
              record->family!=WR_REF_FAMILY_WDS&&
              record->family!=WR_REF_FAMILY_MONITOR))return 0;
 return wr_iot_virtual_open_claim_matches(claim,radio,slots,count);
}
#endif
