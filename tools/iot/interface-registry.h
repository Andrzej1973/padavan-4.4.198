/* Candidate slot mapping. Caller holds adapter lock and pins lifetimes.
 * Release additionally requires caller-proved producer/reference quiescence;
 * IDLE alone does not prove queued callbacks retired. */
#ifndef WR_IOT_INTERFACE_REGISTRY_H
#define WR_IOT_INTERFACE_REGISTRY_H
#include "interface-reference.h"
static inline struct wr_iot_interface_ref *wr_iot_registry_add(
 struct wr_iot_interface_ref *slots,unsigned int count,unsigned long *sequence,
 const void *device){
 unsigned int i;struct wr_iot_interface_ref *free_slot=0;
 if(!slots||!sequence||!device||*sequence==~0UL)return 0;
 for(i=0;i<count;i++){
  if(slots[i].device==device)return 0;
  if(!slots[i].device&&!free_slot)free_slot=&slots[i];
 }
 if(!free_slot)return 0;
 wr_iot_ref_init(free_slot,device,++*sequence);
 return free_slot;
}
/* Production registration must bind a known netdev family at publication.
 * The legacy untyped add helper remains only for host fixtures predating this
 * gate; an UNKNOWN record cannot claim an auxiliary radio open. */
static inline struct wr_iot_interface_ref *wr_iot_registry_add_family(
 struct wr_iot_interface_ref *slots,unsigned int count,unsigned long *sequence,
 const void *device,enum wr_iot_ref_family family){
 struct wr_iot_interface_ref *record;
 if(family<WR_REF_FAMILY_MAIN||family>WR_REF_FAMILY_MONITOR)return 0;
 record=wr_iot_registry_add(slots,count,sequence,device);
 if(record)record->family=family;
 return record;
}
static inline struct wr_iot_interface_ref *wr_iot_registry_find(
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,unsigned long generation){
 unsigned int i;
 if(!slots||!device||!generation)return 0;
 for(i=0;i<count;i++)
  if(slots[i].device==device&&slots[i].generation==generation)return &slots[i];
 return 0;
}
/* Caller holds the adapter transition lock and pins device/adapter lifetime.
 * The returned generation must travel with the UP request and be rechecked
 * at the shared dispatcher before any vendor count or hardware mutation. */
static inline struct wr_iot_interface_ref *wr_iot_registry_find_openable(
 struct wr_iot_interface_ref *slots,unsigned int count,const void *device){
 unsigned int i;
 if(!slots||!device)return 0;
 for(i=0;i<count;i++)
  if(slots[i].device==device&&slots[i].generation&&slots[i].published&&
     !slots[i].removing&&slots[i].phase==WR_REF_IDLE)return &slots[i];
 return 0;
}
/* Caller holds the same adapter lock used for close-ticket admission.
 * Removal intent does not erase an owned reference: ndo_stop must still be
 * able to retire it before unregister may release the slot. */
static inline struct wr_iot_interface_ref *wr_iot_registry_find_owned(
 struct wr_iot_interface_ref *slots,unsigned int count,const void *device){
 unsigned int i;
 if(!slots||!device)return 0;
 for(i=0;i<count;i++)
  if(slots[i].device==device&&slots[i].generation&&slots[i].published&&
     slots[i].phase==WR_REF_OWNED)return &slots[i];
 return 0;
}
/* A last-close decision is valid only when every vendor reference has a
 * published, unambiguous registry owner. RESERVED, CLOSING and uncertain
 * records require their existing operation/recovery owner to finish first.
 * Caller holds the same adapter lock as every vendor count writer. */
static inline int wr_iot_registry_count_matches(
 const struct wr_iot_interface_ref *slots,unsigned int count,
 unsigned int vendor_count){
 unsigned int i,owned=0;
 if(!slots)return 0;
 for(i=0;i<count;i++){
  const struct wr_iot_interface_ref *r=&slots[i];
  if(r->phase==WR_REF_IDLE)continue;
  if(r->phase!=WR_REF_OWNED||!r->device||!r->generation||
     !r->published||r->removing||owned==~0U)return 0;
  owned++;
 }
 return owned==vendor_count;
}
/* Caller holds the adapter lock. A matching removal path must set removing
 * under that SAME lock before unregister. hold() must be nonblocking and pin
 * netdev lifetime (kernel binding: dev_hold); caller releases every pin
 * promptly, before waiting, RTNL acquisition or physical close. This is not
 * itself a PM iterator binding and cannot serialize uninstrumented removals. */
static inline int wr_iot_registry_snapshot(
 const struct wr_iot_interface_ref *slots,unsigned int count,
 const void **devices,unsigned int capacity,void (*hold)(const void *)){
 unsigned int i,used=0;
 if(!slots||!devices||!hold||capacity<count)return -1;
 for(i=0;i<count;i++){
  if(!slots[i].device||!slots[i].published||slots[i].removing)continue;
  hold(slots[i].device);
  devices[used++]=slots[i].device;
 }
 return (int)used;
}
/* Milestones record caller-proven events; these helpers do not perform
 * unregister, drain kernel refs or synchronize vendor workers themselves. */
static inline int wr_iot_registry_begin_remove(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation){
 /* A reserved open still owns the device across unlocked observation/raw UP.
  * Retrying removal after that ticket retires is safe; marking it now is not. */
 /* A prior ndo_stop may already have cleared IFF_UP while its checked
  * continuation still owns the reference. dev_close cannot replay it. */
 if(!r||r->device!=device||!device||!generation||r->generation!=generation||
    (r->phase==WR_REF_RESERVED||r->phase==WR_REF_CLOSING||
     r->phase==WR_REF_UNCERTAIN_OPEN))return 0;
 r->removing=1;return 1;
}
/* Cancel only when the caller proved its attempted teardown made no change.
 * The same adapter lock must exclude a new PM fence/retire while checking
 * pm_or_retiring. Never use this after unregister, beacon free or vendor
 * callback mutation; an already retired record is not resurrected. */
static inline int wr_iot_registry_cancel_remove_unmutated(
 struct wr_iot_interface_ref *r,const void *device,unsigned long generation,
 int pm_or_retiring){
 if(!r||!device||!generation||r->device!=device||
    r->generation!=generation||!r->published||!r->removing||
    r->removal_stage||pm_or_retiring)return 0;
 r->removing=0;return 1;
}
static inline int wr_iot_registry_kernel_done(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation){
 if(!r||r->device!=device||!device||r->generation!=generation||!generation||
    !r->removing||r->phase!=WR_REF_IDLE||r->removal_stage!=0)return 0;
 r->removal_stage=1;return 1;
}
static inline int wr_iot_registry_vendor_done(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation){
 if(!r||r->device!=device||!device||r->generation!=generation||!generation||
    !r->removing||r->phase!=WR_REF_IDLE||r->removal_stage!=1)return 0;
 r->removal_stage=2;return 1;
}
/* Call ONLY after registration callbacks/queued references are quiescent. */
static inline int wr_iot_registry_release(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation){
 if(!r||!device||r->device!=device||!generation||r->generation!=generation||
    r->phase!=WR_REF_IDLE||(r->published&&(!r->removing||r->removal_stage!=2)))return 0;
 wr_iot_ref_init(r,0,0);return 1;
}
#endif
