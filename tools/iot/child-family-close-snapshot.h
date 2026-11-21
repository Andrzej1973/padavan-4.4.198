/* Caller holds transition lock, pins adapter and has fenced new publication.
 * states, when supplied, has count entries indexed exactly like refs.
 * This observes source-model close stages, not hardware/callback quiescence.
 * APCLI/monitor need exact logical completion state in addition to registry.
 * Do not turn this observation into a hardware/callback completion receipt. */
#ifndef WR_IOT_CHILD_FAMILY_CLOSE_SNAPSHOT_H
#define WR_IOT_CHILD_FAMILY_CLOSE_SNAPSHOT_H
#include "interface-registry.h"
#include "aux-family-close.h"
static inline int wr_iot_child_family_close_snapshot(
 const struct wr_iot_interface_ref *refs,unsigned int count,unsigned int family,
 const struct wr_iot_family_close *states,
 unsigned int deferred_owners,int recovery_work_joined,unsigned int *members)
{
 unsigned int i,n=0;
 if(!refs||!members||!count||deferred_owners||!recovery_work_joined)return 0;
 if(family!=WR_REF_FAMILY_APCLI&&family!=WR_REF_FAMILY_WDS&&
    family!=WR_REF_FAMILY_MBSS&&family!=WR_REF_FAMILY_MONITOR)return 0;
 for(i=0;i<count;i++){
  const struct wr_iot_interface_ref *r=&refs[i];
  if(r->family!=family)continue;
  if(!r->device){
   if(r->published||r->removing||r->phase!=WR_REF_IDLE)return 0;
   continue;
  }
  if(!r->generation||!r->published||r->removing||r->phase!=WR_REF_IDLE)return 0;
  if(!wr_iot_registry_checked_close_terminal(r)){
   const struct wr_iot_family_close *state;
   if((family!=WR_REF_FAMILY_APCLI&&family!=WR_REF_FAMILY_MONITOR)||!states)return 0;
   state=&states[i];
   if(r->close_stage!=2||!r->last_token||!r->close_serial||!r->close_epoch||
      state->phase!=WR_FAMILY_CLOSE_DONE||state->device!=r->device||
      state->family!=r->family||state->generation!=r->generation||
      state->token!=r->last_token||state->serial!=r->close_serial||
      state->epoch!=r->close_epoch)return 0;
  }
  n++;
 }
 *members=n;return 1;
}
#endif
