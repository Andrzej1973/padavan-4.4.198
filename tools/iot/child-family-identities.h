/* Software identity snapshot only. Caller fences registration and holds the
 * same registry lock across each operation; callbacks/hardware are separate. */
#ifndef WR_IOT_CHILD_FAMILY_IDENTITIES_H
#define WR_IOT_CHILD_FAMILY_IDENTITIES_H
#include "child-family-close-snapshot.h"
struct wr_iot_child_identity {const void *device;unsigned long generation;unsigned int slot,family;};
static inline int wr_iot_child_family_capture(
 const struct wr_iot_interface_ref *refs,unsigned int count,unsigned int family,
 const struct wr_iot_family_close *states,unsigned int deferred,int joined,
 struct wr_iot_child_identity *ids,unsigned int capacity,unsigned int *used)
{
 unsigned int i,n=0,members;
 if(!ids||!used||!wr_iot_child_family_close_snapshot(refs,count,family,states,deferred,joined,&members)||members>capacity)return 0;
 for(i=0;i<count;i++)if(refs[i].family==family&&refs[i].device){
  ids[n].device=refs[i].device;ids[n].generation=refs[i].generation;
  ids[n].slot=i;ids[n].family=family;n++;
 }
 *used=n;return 1;
}
/* Requires exact original slot to be empty and all records of that family
 * retired. A new generation in a reused slot is NOT the old completion. */
static inline int wr_iot_child_family_registry_empty(
 const struct wr_iot_interface_ref *refs,unsigned int count,unsigned int family,
 const struct wr_iot_child_identity *ids,unsigned int used)
{
 unsigned int i,j;
 if(!refs||!count||!ids)return 0;
 if(family!=WR_REF_FAMILY_APCLI&&family!=WR_REF_FAMILY_WDS&&
    family!=WR_REF_FAMILY_MBSS&&family!=WR_REF_FAMILY_MONITOR)return 0;
 for(i=0;i<used;i++){
  const struct wr_iot_interface_ref *r;
  if(!ids[i].device||!ids[i].generation||ids[i].family!=family||ids[i].slot>=count)return 0;
  for(j=0;j<i;j++)if(ids[i].slot==ids[j].slot)return 0;
  r=&refs[ids[i].slot];
  if(r->device||r->generation||r->published||r->removing||r->phase!=WR_REF_IDLE)return 0;
 }
 for(i=0;i<count;i++)if(refs[i].family==family&&
   (refs[i].device||refs[i].published||refs[i].removing||refs[i].phase!=WR_REF_IDLE))return 0;
 return 1;
}
#endif
