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
};
/* Fresh/quiescent registration only. */
static inline void wr_iot_wds_peer_operation_init(
 struct wr_iot_wds_peer_operation *s,const void *device,unsigned long generation){
 s->device=device;s->generation=generation;s->active=0;s->removing=0;
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
#endif
