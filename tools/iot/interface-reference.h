/* Candidate bookkeeping, not installed in netdevice wrappers.
 * Caller holds common adapter transition lock and pins device/adapter.
 * registration generation is NOT radio epoch: reset must not erase an owned
 * UP reference while an administratively opened interface still exists.
 * Initialize only a fresh/quiescent registration; never reset live records. */
#ifndef WR_IOT_INTERFACE_REFERENCE_H
#define WR_IOT_INTERFACE_REFERENCE_H
enum wr_iot_ref_phase {WR_REF_IDLE,WR_REF_RESERVED,WR_REF_OWNED,WR_REF_CLOSING};
struct wr_iot_interface_ref {
 const void *device;
 unsigned long generation,last_token,close_serial;
 unsigned int published,removing,removal_stage,close_stage;
 enum wr_iot_ref_phase phase;
};
static inline void wr_iot_ref_init(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation){
 r->device=device;r->generation=generation;r->last_token=0;r->close_serial=0;r->close_stage=0;r->published=0;r->removing=0;r->removal_stage=0;r->phase=WR_REF_IDLE;
}
static inline int wr_iot_ref_matches(const struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token){
 return device&&r->device==device&&generation&&r->generation==generation&&
        token&&r->last_token==token;
}
static inline int wr_iot_ref_reserve(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token){
 if(!device||r->device!=device||!generation||r->generation!=generation||
    !token||token<=r->last_token||r->removing||r->phase!=WR_REF_IDLE)return 0;
 r->last_token=token;r->close_serial=0;r->close_stage=0;r->phase=WR_REF_RESERVED;return 1;
}
/* acquired describes successful vendor UP, even if later setup fails.
 * Such a reference needs normal checked close/rollback, not an idle reset. */
static inline int wr_iot_ref_open_finish(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token,int acquired){
 if(!wr_iot_ref_matches(r,device,generation,token)||r->phase!=WR_REF_RESERVED)return 0;
 r->phase=acquired?WR_REF_OWNED:WR_REF_IDLE;return 1;
}
static inline int wr_iot_ref_begin_close(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token){
 if(!wr_iot_ref_matches(r,device,generation,token)||r->phase!=WR_REF_OWNED)return 0;
 r->phase=WR_REF_CLOSING;return 1;
}
/* Call only AFTER checked DOWN succeeds. Failed DOWN leaves CLOSING intact. */
static inline int wr_iot_ref_consume(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token){
 if(!wr_iot_ref_matches(r,device,generation,token)||r->phase!=WR_REF_CLOSING)return 0;
 r->phase=WR_REF_IDLE;return 1;
}
#endif
