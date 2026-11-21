/* Host-only AP-client/monitor family-close ordering contract.
 * APC_CLOSE and SNIFF_CLOSE may mutate state before reporting failure.
 * This model cannot establish physical or callback quiescence. */
#ifndef WR_IOT_AUX_FAMILY_CLOSE_H
#define WR_IOT_AUX_FAMILY_CLOSE_H
#include "interface-reference.h"

enum wr_iot_family_close_phase {
 WR_FAMILY_CLOSE_IDLE, WR_FAMILY_CLOSE_IN_FLIGHT,
 WR_FAMILY_CLOSE_UNCERTAIN, WR_FAMILY_CLOSE_CONFIRMED,
 WR_FAMILY_DOWN_IN_FLIGHT, WR_FAMILY_DOWN_RETRY,
 WR_FAMILY_DOWN_CONFIRMED, WR_FAMILY_CLOSE_DONE
};
struct wr_iot_family_close {
 const void *device;
 unsigned long generation,serial,epoch,token;
 enum wr_iot_ref_family family;
 enum wr_iot_family_close_phase phase;
};
static inline void wr_iot_family_close_init(struct wr_iot_family_close *state){
 state->device=0;state->generation=0;state->serial=0;state->epoch=0;state->token=0;
 state->family=WR_REF_FAMILY_UNKNOWN;state->phase=WR_FAMILY_CLOSE_IDLE;
}
static inline int wr_iot_family_close_matches(
 const struct wr_iot_family_close *state,
 const struct wr_iot_interface_ref *record){
 return state&&record&&state->device&&
        state->device==record->device&&
        state->generation==record->generation&&
        state->serial==record->close_serial&&
        state->epoch==record->close_epoch&&state->token==record->last_token&&
        record->published&&
        state->family==record->family&&
        record->phase==WR_REF_CLOSING;
}
/* Called under the adapter lock before any family ioctl is invoked. */
static inline int wr_iot_family_close_begin(
 struct wr_iot_family_close *state,
 const struct wr_iot_interface_ref *record){
 if(!state||!record||state->phase!=WR_FAMILY_CLOSE_IDLE||
    (record->family!=WR_REF_FAMILY_APCLI&&
     record->family!=WR_REF_FAMILY_MONITOR)||
    !record->device||!record->generation||!record->close_serial||
    !record->close_epoch||!record->last_token||!record->published||
    record->phase!=WR_REF_CLOSING)return 0;
 state->device=record->device;state->generation=record->generation;
 state->serial=record->close_serial;state->family=record->family;
 state->epoch=record->close_epoch;state->token=record->last_token;
 state->phase=WR_FAMILY_CLOSE_IN_FLIGHT;return 1;
}
/* Failure is uncertain: never replay a possibly mutating family ioctl. */
static inline int wr_iot_family_close_result(
 struct wr_iot_family_close *state,
 const struct wr_iot_interface_ref *record,int success){
 if(!wr_iot_family_close_matches(state,record)||
    state->phase!=WR_FAMILY_CLOSE_IN_FLIGHT)return 0;
 state->phase=success?WR_FAMILY_CLOSE_CONFIRMED:WR_FAMILY_CLOSE_UNCERTAIN;
 return 1;
}
static inline int wr_iot_family_down_begin(
 struct wr_iot_family_close *state,
 const struct wr_iot_interface_ref *record){
 if(!wr_iot_family_close_matches(state,record)||
    (state->phase!=WR_FAMILY_CLOSE_CONFIRMED&&
     state->phase!=WR_FAMILY_DOWN_RETRY))return 0;
 state->phase=WR_FAMILY_DOWN_IN_FLIGHT;return 1;
}
/* A failed checked DOWN needs same-ticket reconciliation before retry. */
static inline int wr_iot_family_down_result(
 struct wr_iot_family_close *state,
 const struct wr_iot_interface_ref *record,int verified_success,
 int proven_unmutated_failure){
 if(!wr_iot_family_close_matches(state,record)||
    state->phase!=WR_FAMILY_DOWN_IN_FLIGHT||
    (verified_success&&proven_unmutated_failure))return 0;
 state->phase=verified_success?WR_FAMILY_DOWN_CONFIRMED:
              proven_unmutated_failure?WR_FAMILY_DOWN_RETRY:
              WR_FAMILY_CLOSE_UNCERTAIN;
 return 1;
}
static inline int wr_iot_family_close_finish(
 struct wr_iot_family_close *state,
 const struct wr_iot_interface_ref *record){
 if(!wr_iot_family_close_matches(state,record)||
    state->phase!=WR_FAMILY_DOWN_CONFIRMED)return 0;
 state->phase=WR_FAMILY_CLOSE_DONE;return 1;
}
#endif
