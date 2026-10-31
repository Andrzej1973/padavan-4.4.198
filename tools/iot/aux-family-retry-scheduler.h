/* Host-only lifetime contract for deferred APCLI/Monitor close retry.
 * The caller pins the adapter and netdev, retains the original ndo_open
 * module reference, and fences adapter release before queueing. This model
 * does not install a work_struct or prove RTNL, callback or DMA quiescence. */
#ifndef WR_IOT_AUX_FAMILY_RETRY_SCHEDULER_H
#define WR_IOT_AUX_FAMILY_RETRY_SCHEDULER_H
#include "interface-reference.h"
#include "aux-family-close.h"

enum wr_iot_aux_retry_phase {
 WR_AUX_RETRY_IDLE,WR_AUX_RETRY_QUEUED,WR_AUX_RETRY_RUNNING,
 WR_AUX_RETRY_RETAINED,WR_AUX_RETRY_STOPPING
};

struct wr_iot_aux_retry_owner {
 const void *device;
 unsigned long generation,serial,epoch,token;
 enum wr_iot_ref_family family;
 unsigned int deferred_owners,attempts,failed_submissions;
 int netdev_held,module_pin_held,adapter_release_fenced;
 int stop_requested,action_claimed,completed,work_joined;
 enum wr_iot_aux_retry_phase phase;
};

static inline void wr_iot_aux_retry_init(
 struct wr_iot_aux_retry_owner *owner){
 owner->device=0;owner->generation=0;owner->serial=0;owner->epoch=0;
 owner->token=0;owner->family=WR_REF_FAMILY_UNKNOWN;
 owner->deferred_owners=0;owner->attempts=0;owner->failed_submissions=0;
 owner->netdev_held=0;owner->module_pin_held=0;
 owner->adapter_release_fenced=0;owner->stop_requested=0;owner->action_claimed=0;
 owner->completed=0;owner->work_joined=0;
 owner->phase=WR_AUX_RETRY_IDLE;
}

static inline int wr_iot_aux_retry_matches(
 const struct wr_iot_aux_retry_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_family_close *state){
 return owner&&record&&state&&owner->device&&
        owner->device==record->device&&
        owner->family==record->family&&
        owner->family==state->family&&
        (owner->family==WR_REF_FAMILY_APCLI||
         owner->family==WR_REF_FAMILY_MONITOR)&&
        owner->generation==record->generation&&
        owner->serial==record->close_serial&&
        owner->epoch==record->close_epoch&&
        owner->token==record->last_token&&
        state->device==record->device&&
        state->generation==record->generation&&
        state->serial==record->close_serial&&
        state->epoch==record->close_epoch&&
        state->token==record->last_token&&
        record->published&&record->phase==WR_REF_CLOSING&&
        record->close_stage==1&&
        state->phase==WR_FAMILY_DOWN_RETRY;
}

/* Call after dev_hold and before schedule_work. Keep all three ownership
 * claims if scheduling is rejected or the worker later fails. */
static inline int wr_iot_aux_retry_queue(
 struct wr_iot_aux_retry_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_family_close *state,
 int netdev_held,int module_pin_held,int adapter_release_fenced){
 if(!owner||!record||!state||owner->phase!=WR_AUX_RETRY_IDLE||
    owner->device||owner->deferred_owners||owner->stop_requested||
    !netdev_held||!module_pin_held||!adapter_release_fenced)return 0;
 owner->device=record->device;owner->generation=record->generation;
 owner->serial=record->close_serial;owner->epoch=record->close_epoch;
 owner->token=record->last_token;owner->family=record->family;
 owner->deferred_owners=1;owner->attempts=0;
 owner->failed_submissions=0;owner->netdev_held=1;
 owner->module_pin_held=1;owner->adapter_release_fenced=1;
 owner->stop_requested=0;owner->action_claimed=0;
 owner->completed=0;owner->work_joined=0;
 owner->phase=WR_AUX_RETRY_QUEUED;
 if(wr_iot_aux_retry_matches(owner,record,state))return 1;
 wr_iot_aux_retry_init(owner);return 0;
}

/* A rejected submission is not completion. Preserve every claim for an
 * explicit stop/join decision or a later bounded retry policy. */
static inline int wr_iot_aux_retry_schedule_result(
 struct wr_iot_aux_retry_owner *owner,int accepted){
 if(!owner||owner->phase!=WR_AUX_RETRY_QUEUED)return 0;
 if(accepted)return 1;
 owner->failed_submissions++;
 owner->phase=WR_AUX_RETRY_RETAINED;
 return 1;
}

static inline int wr_iot_aux_retry_begin(
 struct wr_iot_aux_retry_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_family_close *state){
 if(!owner||owner->phase!=WR_AUX_RETRY_QUEUED||
    owner->stop_requested||!owner->deferred_owners||
    !wr_iot_aux_retry_matches(owner,record,state))return 0;
 owner->phase=WR_AUX_RETRY_RUNNING;owner->attempts++;
 return 1;
}

/* The worker may call only the family-specific exact-ticket Retry helper.
 * It must not call dev_close, restart APC_CLOSE/SNIFF_CLOSE or replay HNAT. */
static inline int wr_iot_aux_retry_action(
 struct wr_iot_aux_retry_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_family_close *state){
 if(!owner||owner->action_claimed||owner->phase!=WR_AUX_RETRY_RUNNING||
    owner->stop_requested||owner->completed||!owner->deferred_owners||
    !wr_iot_aux_retry_matches(owner,record,state))return 0;
 owner->action_claimed=1;
 return 1;
}

static inline int wr_iot_aux_retry_retain(
 struct wr_iot_aux_retry_owner *owner){
 if(!owner||owner->phase!=WR_AUX_RETRY_RUNNING||
    owner->completed||!owner->deferred_owners)return 0;
 owner->phase=owner->stop_requested?
  WR_AUX_RETRY_STOPPING:WR_AUX_RETRY_RETAINED;
 return 1;
}

/* A worker that cannot begin or claim its exact ticket leaves every resource
 * retained. This also records a cancellation that raced with queueing. */
static inline int wr_iot_aux_retry_abandon(
 struct wr_iot_aux_retry_owner *owner){
 if(!owner||!owner->deferred_owners||owner->completed)return 0;
 if(owner->phase==WR_AUX_RETRY_RETAINED||
    owner->phase==WR_AUX_RETRY_STOPPING)return 1;
 if(owner->phase==WR_AUX_RETRY_RUNNING)return wr_iot_aux_retry_retain(owner);
 if(owner->phase!=WR_AUX_RETRY_QUEUED)return 0;
 owner->phase=owner->stop_requested?
  WR_AUX_RETRY_STOPPING:WR_AUX_RETRY_RETAINED;
 return 1;
}

static inline int wr_iot_aux_retry_request_stop(
 struct wr_iot_aux_retry_owner *owner){
 if(!owner||owner->phase==WR_AUX_RETRY_IDLE)return 0;
 owner->stop_requested=1;
 if(owner->phase==WR_AUX_RETRY_QUEUED||
    owner->phase==WR_AUX_RETRY_RETAINED)
  owner->phase=WR_AUX_RETRY_STOPPING;
 return 1;
}

/* Success means the exact-ticket helper consumed its ticket and released
 * the original module pin. The netdev hold is released only after join. */
static inline int wr_iot_aux_retry_mark_completed(
 struct wr_iot_aux_retry_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_family_close *state,int module_pin_released){
 if(!owner||!record||!state||!module_pin_released||owner->completed||
    (owner->phase!=WR_AUX_RETRY_RUNNING&&
     owner->phase!=WR_AUX_RETRY_STOPPING)||
    !owner->deferred_owners||!owner->action_claimed||
    owner->device!=record->device||
    owner->generation!=record->generation||
    owner->serial!=record->close_serial||
    owner->epoch!=record->close_epoch||
    owner->token!=record->last_token||
    owner->family!=record->family||
    owner->family!=state->family||
    record->phase!=WR_REF_IDLE||record->close_stage!=2||
    state->device!=owner->device||
    state->generation!=owner->generation||
    state->serial!=owner->serial||
    state->epoch!=owner->epoch||state->token!=owner->token||
    state->phase!=WR_FAMILY_CLOSE_DONE)return 0;
 owner->completed=1;owner->module_pin_held=0;return 1;
}

/* Returns 1 and sets drop_netdev when a joined successful worker may release
 * its hold. A stopped or failed owner remains retained and fails closed. */
static inline int wr_iot_aux_retry_complete(
 struct wr_iot_aux_retry_owner *owner,int work_joined,int *drop_netdev){
 if(!owner||!drop_netdev||!work_joined||!owner->completed||
    !owner->deferred_owners||!owner->netdev_held||owner->module_pin_held)
  return 0;
 *drop_netdev=1;wr_iot_aux_retry_init(owner);return 1;
}

/* Adapter release must observe an empty owner, or a joined completed worker
 * that has already dropped its deferred-owner count. */
static inline int wr_iot_aux_retry_release_ready(
 const struct wr_iot_aux_retry_owner *owner,int work_joined){
 if(!owner)return 0;
 return owner->phase==WR_AUX_RETRY_IDLE&&!owner->deferred_owners&&
        !owner->netdev_held&&!owner->module_pin_held&&!owner->device&&
        !owner->completed&&(!owner->work_joined||work_joined);
}

#endif
