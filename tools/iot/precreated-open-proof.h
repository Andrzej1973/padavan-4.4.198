/* One-use association between an immutable request and an existing BSS_OPEN
 * claim. All calls require the adapter transition lock, pinned device/adapter
 * and a separately held task/configuration lease excluding credential setters.
 * Observation runs outside this lock. This token performs no driver mutation,
 * allocates no new radio ticket and grants no protection against unbound writers. */
#ifndef WR_IOT_PRECREATED_OPEN_PROOF_H
#define WR_IOT_PRECREATED_OPEN_PROOF_H
#include "virtual-open-claim.h"
struct wr_iot_precreated_open_proof {
 struct wr_iot_virtual_open_claim claim;
 unsigned long long request_generation;
 unsigned int pending;
};
static inline int wr_iot_precreated_open_current(
 const struct wr_iot_virtual_open_claim *claim,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,const void *iot_device)
{
 struct wr_iot_interface_ref *record;
 if(!iot_device||!claim||claim->device!=iot_device||claim->operation!=WR_RADIO_BSS_OPEN||
    !wr_iot_virtual_open_claim_matches(claim,radio,slots,count))return 0;
 record=wr_iot_registry_find(slots,count,iot_device,claim->generation);
 return record&&record->family==WR_REF_FAMILY_MBSS;
}
static inline int wr_iot_precreated_open_observe_begin(
 struct wr_iot_precreated_open_proof *proof,
 const struct wr_iot_virtual_open_claim *claim,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,const void *iot_device,
 unsigned long long request_generation)
{
 if(!proof||proof->pending||!request_generation||
    !wr_iot_precreated_open_current(claim,radio,slots,count,iot_device))return 0;
 proof->claim=*claim;proof->request_generation=request_generation;proof->pending=1;
 return 1;
}
static inline int wr_iot_precreated_open_observe_finish(
 struct wr_iot_precreated_open_proof *proof,
 const struct wr_iot_virtual_open_claim *claim,
 const struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int count,const void *iot_device,
 unsigned long long request_generation,int observed)
{
 int matches;
 if(!proof||!proof->pending)return 0;
 /* Consume on every attempt, including refusal. Retry requires new begin. */
 proof->pending=0;
 matches=observed==1&&request_generation&&request_generation==proof->request_generation&&
  claim&&claim->device==proof->claim.device&&claim->generation==proof->claim.generation&&
  claim->serial==proof->claim.serial&&claim->epoch==proof->claim.epoch&&
  claim->operation==proof->claim.operation&&
  wr_iot_precreated_open_current(claim,radio,slots,count,iot_device);
 proof->request_generation=0;
 return matches;
}
#endif
