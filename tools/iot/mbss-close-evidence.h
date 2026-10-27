/* Host-only MBSS close evidence before family removal. The caller holds the
 * shared adapter transition lock, fences admission and supplies the vendor's
 * published MBSS count. This does not drain callbacks or bind vendor code. */
#ifndef WR_IOT_MBSS_CLOSE_EVIDENCE_H
#define WR_IOT_MBSS_CLOSE_EVIDENCE_H
#include "interface-registry.h"

static inline int wr_iot_mbss_closes_joined(
 const struct wr_iot_interface_ref *slots, unsigned int count,
 unsigned int published_expected, int recovery_joined){
 unsigned int i, seen=0;
 if(!slots||!recovery_joined||published_expected>count)return 0;
 for(i=0;i<count;i++){
  const struct wr_iot_interface_ref *r=&slots[i];
  if(!r->published){
   if(r->family==WR_REF_FAMILY_MBSS&&r->phase!=WR_REF_IDLE)return 0;
   continue;
  }
  /* Unknown ownership can hide a live MBSS reference. */
  if(r->family==WR_REF_FAMILY_UNKNOWN)return 0;
  if(r->family!=WR_REF_FAMILY_MBSS)continue;
  if(!r->device||!r->generation||r->phase!=WR_REF_IDLE||
     r->close_running||r->removal_stage||seen==~0U)return 0;
  seen++;
 }
 return seen==published_expected;
}
#endif
