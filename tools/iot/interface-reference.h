/* Candidate bookkeeping, not installed in netdevice wrappers.
 * Caller holds common adapter transition lock and pins device/adapter.
 * registration generation is NOT radio epoch: reset must not erase an owned
 * UP reference while an administratively opened interface still exists.
 * Initialize only a fresh/quiescent registration; never reset live records. */
#ifndef WR_IOT_INTERFACE_REFERENCE_H
#define WR_IOT_INTERFACE_REFERENCE_H
enum wr_iot_ref_phase {WR_REF_IDLE,WR_REF_RESERVED,WR_REF_OWNED,WR_REF_CLOSING,
                       WR_REF_UNCERTAIN_OPEN};
enum wr_iot_ref_family {WR_REF_FAMILY_UNKNOWN,WR_REF_FAMILY_MAIN,
 WR_REF_FAMILY_MBSS,WR_REF_FAMILY_APCLI,WR_REF_FAMILY_WDS,
 WR_REF_FAMILY_MONITOR};
struct wr_iot_interface_ref {
 const void *device;
 unsigned long generation,last_token,close_serial;
 unsigned long close_epoch;
 unsigned int close_vendor_count;
 int close_prior_phase,close_prior_ready;
 unsigned int published,removing,removal_stage,close_stage;
 /* Set only by a caller-proven pre-acquisition failure. An idle record with
  * an old token is otherwise not proof that an acquired open was closed. */
 unsigned int open_unmutated;
 enum wr_iot_ref_phase phase;
 enum wr_iot_ref_family family;
};
static inline void wr_iot_ref_init(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation){
 r->device=device;r->generation=generation;r->last_token=0;r->close_serial=0;r->close_epoch=0;r->close_vendor_count=0;r->close_prior_phase=0;r->close_prior_ready=0;r->close_stage=0;r->open_unmutated=0;r->published=0;r->removing=0;r->removal_stage=0;r->phase=WR_REF_IDLE;r->family=WR_REF_FAMILY_UNKNOWN;
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
 r->last_token=token;r->close_serial=0;r->close_epoch=0;
 r->close_vendor_count=0;r->close_prior_phase=0;r->close_prior_ready=0;
 r->close_stage=0;r->open_unmutated=0;r->phase=WR_REF_RESERVED;return 1;
}
/* acquired describes successful vendor UP, even if later setup fails.
 * Such a reference needs normal checked close/rollback, not an idle reset. */
static inline int wr_iot_ref_open_finish(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token,int acquired){
 if(!wr_iot_ref_matches(r,device,generation,token)||r->phase!=WR_REF_RESERVED)return 0;
 r->phase=acquired?WR_REF_OWNED:WR_REF_IDLE;
 r->open_unmutated=acquired?0U:1U;return 1;
}
/* Vendor-specific abort failed after open mutation. Retain the registration,
 * module pin and token until a separate recovery owner proves teardown. */
static inline int wr_iot_ref_open_uncertain(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token){
 if(!r||!wr_iot_ref_matches(r,device,generation,token)||
    r->phase!=WR_REF_RESERVED)return 0;
 r->phase=WR_REF_UNCERTAIN_OPEN;return 1;
}
/* Main open calls AP_MAIN_OPEN before the virtual-UP dispatcher. Once that
 * call begins, even an IRQ or rt28xx_init failure is not proven unmutated.
 * Keep the module pin for ACQUIRED and UNCERTAIN outcomes; only a failure
 * known to precede AP_MAIN_OPEN may release it. This is host-side policy;
 * the vendor wrapper still needs a checked recovery owner before binding. */
enum wr_iot_main_open_outcome {
 WR_MAIN_OPEN_UNMUTATED_FAILURE,
 WR_MAIN_OPEN_ACQUIRED,
 WR_MAIN_OPEN_UNCERTAIN_FAILURE
};
static inline int wr_iot_ref_complete_main_open(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token,
 enum wr_iot_main_open_outcome outcome,int *retain_pin){
 if(!retain_pin||!r||!wr_iot_ref_matches(r,device,generation,token)||
    r->phase!=WR_REF_RESERVED)return 0;
 switch(outcome){
 case WR_MAIN_OPEN_UNMUTATED_FAILURE:
  r->phase=WR_REF_IDLE;r->open_unmutated=1;*retain_pin=0;return 1;
 case WR_MAIN_OPEN_ACQUIRED:
  r->phase=WR_REF_OWNED;*retain_pin=1;return 1;
 case WR_MAIN_OPEN_UNCERTAIN_FAILURE:
  r->phase=WR_REF_UNCERTAIN_OPEN;*retain_pin=1;return 1;
 default:return 0;
 }
}
/* AP-client/monitor have a family OPEN after virtual-UP; WDS does not.
 * Only a failure BEFORE any required call is known unmutated. A failed
 * operation after an attempt retains the reference and module pin for checked
 * recovery; ndo_stop will not follow a failed ndo_open. */
static inline int wr_iot_ref_complete_aux_open(struct wr_iot_interface_ref *r,
 const void *device,unsigned long generation,unsigned long token,
 int family_open_required,int virtual_up_attempted,int virtual_up_succeeded,
 int family_open_attempted,int family_open_succeeded,int *retain_pin){
 if(!r||!retain_pin||!wr_iot_ref_matches(r,device,generation,token)||
    r->phase!=WR_REF_RESERVED||
    (family_open_required!=0&&family_open_required!=1)||
    (virtual_up_succeeded&&!virtual_up_attempted)||
    (family_open_succeeded&&!family_open_attempted)||
    (!family_open_required&&(family_open_attempted||family_open_succeeded)))return 0;
 if(!virtual_up_attempted&&!family_open_attempted){
  r->phase=WR_REF_IDLE;r->open_unmutated=1;*retain_pin=0;
 }else if(virtual_up_succeeded&&
           (!family_open_required||family_open_succeeded)){
  r->phase=WR_REF_OWNED;*retain_pin=1;
 }else{
  r->phase=WR_REF_UNCERTAIN_OPEN;*retain_pin=1;
 }
 return 1;
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
