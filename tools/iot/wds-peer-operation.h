/* Candidate operation ownership. All access uses the adapter transition lock.
 * The caller separately pins adapter/netdev and must bind this state to the
 * complete outer WDS insertion and removal; this is not callback quiescence. */
#ifndef WR_IOT_WDS_PEER_OPERATION_H
#define WR_IOT_WDS_PEER_OPERATION_H
struct wr_iot_wds_peer_operation {
 const void *device;
 unsigned long generation;
 unsigned int active;
 int removing;
 /* Saved retirement identity survives the synchronous caller on failure. */
 unsigned long retirement_serial;
 unsigned int retirement_stage,retirement_index,retirement_wcid;
 unsigned char retirement_address[6];
 unsigned int retirement_hardware_observed;
 int retirement_hardware_result;
 unsigned int retirement_retry_count,retirement_retry_observed;
 int retirement_retry_result;
};
/* Fresh/quiescent registration only. */
static inline void wr_iot_wds_peer_operation_init(
 struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation){
 s->device=device;s->generation=generation;s->active=0;s->removing=0;
 s->retirement_serial=0;s->retirement_stage=0;
 s->retirement_index=0;s->retirement_wcid=0;
 s->retirement_hardware_observed=0;s->retirement_hardware_result=0;
 s->retirement_retry_count=0;s->retirement_retry_observed=0;s->retirement_retry_result=0;
 {unsigned int i;for(i=0;i<6;i++)s->retirement_address[i]=0;}
}
static inline int wr_iot_wds_peer_operation_enter(
 struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation){
 if(!s||!device||!generation||s->device!=device||s->generation!=generation||
    s->removing||s->active==~0U)return 0;
 s->active++;return 1;
}
static inline int wr_iot_wds_peer_operation_leave(
 struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation){
 if(!s||!device||!generation||s->device!=device||s->generation!=generation||
    !s->active)return 0;
 s->active--;return 1;
}
/* Atomic admission: refusal leaves no half-published removal intent. */
static inline int wr_iot_wds_peer_operation_begin_remove(
 struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation){
 if(!s||!device||!generation||s->device!=device||s->generation!=generation||
    s->active||s->removing)return 0;
 s->removing=1;return 1;
}
/* Save under the same lock, before deletion. Serial is never reused within
 * a registration. Refuse overflow instead of making an old completion valid. */
static inline unsigned long wr_iot_wds_retirement_save(
 struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation,
 unsigned int index,unsigned int wcid,const unsigned char *address){
 unsigned int i;
 if(!s||!device||!address||!generation||s->device!=device||s->generation!=generation||
    !s->removing||s->active||s->retirement_stage||s->retirement_serial==~0UL||!wcid)return 0;
 s->retirement_serial++;s->retirement_index=index;s->retirement_wcid=wcid;
 s->retirement_hardware_observed=0;s->retirement_hardware_result=0;
 s->retirement_retry_count=0;s->retirement_retry_observed=0;s->retirement_retry_result=0;
 for(i=0;i<6;i++)s->retirement_address[i]=address[i];
 s->retirement_stage=1;return s->retirement_serial;
}
static inline int wr_iot_wds_retirement_matches(
 const struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation,
 unsigned long serial,unsigned int index,unsigned int wcid,const unsigned char *address){
 unsigned int i;
 if(!s||!device||!address||!generation||!serial||s->device!=device||s->generation!=generation||
    !s->removing||s->active||!s->retirement_stage||s->retirement_serial!=serial||
    s->retirement_index!=index||s->retirement_wcid!=wcid)return 0;
 for(i=0;i<6;i++)if(s->retirement_address[i]!=address[i])return 0;
 return 1;
}
/* Preserve the first hardware result; absence remains distinct from APPLIED. */
static inline int wr_iot_wds_retirement_hardware_result(
 struct wr_iot_wds_peer_operation *s,unsigned long serial,int result){
 if(s&&serial&&s->retirement_serial==serial&&s->retirement_stage==3&&
    s->removing&&!s->active&&!s->retirement_retry_observed){
  s->retirement_retry_observed=1;s->retirement_retry_result=result;
  if(result!=0)s->retirement_stage=2;
  return 1;
 }
 if(!s||!serial||s->retirement_serial!=serial||s->retirement_stage!=1||
    !s->removing||s->active||s->retirement_hardware_observed)return 0;
 s->retirement_hardware_result=result;s->retirement_hardware_observed=1;return 1;
}
/* Only NOT_WRITTEN (-1) may re-enter the hardware checkpoint. PARTIAL and
 * unobserved failures remain retained. All callers hold transition lock. */
static inline int wr_iot_wds_retirement_claim_no_write(
 struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation,
 unsigned long serial,unsigned int index,unsigned int wcid,const unsigned char *address){
 if(!wr_iot_wds_retirement_matches(s,device,generation,serial,index,wcid,address)||
    s->retirement_stage!=2||!s->retirement_hardware_observed||
    (s->retirement_retry_observed?s->retirement_retry_result:s->retirement_hardware_result)!=-1||
    s->retirement_retry_count==~0U)return 0;
 s->retirement_retry_count++;s->retirement_retry_observed=0;s->retirement_retry_result=0;
 s->retirement_stage=3;return 1;
}
/* This milestone is after the real software deletion, not just WTBL success. */
static inline int wr_iot_wds_retirement_software_done(
 struct wr_iot_wds_peer_operation *s,unsigned long serial){
 if(!s||!serial||s->retirement_serial!=serial||s->retirement_stage!=3||
    !s->removing||s->active||!s->retirement_retry_observed||s->retirement_retry_result!=0)return 0;
 s->retirement_stage=4;return 1;
}
/* Stage 2 retains exact identity for a future checked continuation. This
 * records uncertainty; it does not authorize replay of vendor deletion. */
static inline int wr_iot_wds_retirement_retain(
 struct wr_iot_wds_peer_operation *s,unsigned long serial){
 if(!s||!serial||s->retirement_serial!=serial||s->retirement_stage!=1||!s->removing)return 0;
 s->retirement_stage=2;return 1;
}
/* Only after caller proves exact-slot completion under all required locks. */
static inline int wr_iot_wds_retirement_complete(
 struct wr_iot_wds_peer_operation *s,unsigned long serial){
 if(!s||!serial||s->retirement_serial!=serial||
    (s->retirement_stage!=1&&s->retirement_stage!=4)||!s->removing||s->active)return 0;
 s->retirement_stage=0;s->removing=0;return 1;
}
#endif
