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
static inline struct wr_iot_interface_ref *wr_iot_registry_find(
 struct wr_iot_interface_ref *slots,unsigned int count,
 const void *device,unsigned long generation){
 unsigned int i;
 if(!slots||!device||!generation)return 0;
 for(i=0;i<count;i++)
  if(slots[i].device==device&&slots[i].generation==generation)return &slots[i];
 return 0;
}
/* Milestones record caller-proven events; these helpers do not perform
 * unregister, drain kernel refs or synchronize vendor workers themselves. */
static inline int wr_iot_registry_begin_remove(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation){
 if(!r||r->device!=device||!device||!generation||r->generation!=generation)return 0;
 r->removing=1;return 1;
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
