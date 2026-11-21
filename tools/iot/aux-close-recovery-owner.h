/* Host-only lifetime contract for a deferred auxiliary close continuation.
 * No work_struct or vendor binding is installed by this model. All functions
 * run under the common adapter lock. An actual caller must acquire dev_hold
 * before queueing, keep the open module pin, and make EVERY adapter free path
 * obey deferred_owners before this contract can be bound. */
#ifndef WR_IOT_AUX_CLOSE_RECOVERY_OWNER_H
#define WR_IOT_AUX_CLOSE_RECOVERY_OWNER_H
#include "interface-reference.h"
#include "radio-transition.h"

enum wr_iot_recovery_phase {
 WR_RECOVERY_IDLE,WR_RECOVERY_QUEUED,WR_RECOVERY_RUNNING,
 WR_RECOVERY_RETAINED,WR_RECOVERY_STOPPING
};
enum wr_iot_recovery_action {
 WR_RECOVERY_NO_ACTION,WR_RECOVERY_RETRY_DOWN,
 WR_RECOVERY_COMPLETE_AFTER_DOWN
};
struct wr_iot_aux_close_recovery {
 const void *device;
 unsigned long generation,serial;
 enum wr_iot_ref_family family;
 unsigned int deferred_owners,attempts;
 int stop_requested,completed;
 enum wr_iot_recovery_phase phase;
};
static inline void wr_iot_aux_close_recovery_init(
 struct wr_iot_aux_close_recovery *owner){
 owner->device=0;owner->generation=0;owner->serial=0;
 owner->family=WR_REF_FAMILY_UNKNOWN;
 owner->deferred_owners=0;owner->attempts=0;
 owner->stop_requested=0;owner->completed=0;
 owner->phase=WR_RECOVERY_IDLE;
}
/* WDS only. AP-client runs APC_CLOSE (MLME disconnect and other mutations)
 * before virtual DOWN; monitor runs SNIFF_CLOSE (RX-filter mutation) first.
 * Neither family may reuse the WDS retry stages without its own checked
 * family-close result and partial-side-effect reconciliation.
 * The caller has already taken a netdev reference and installed an adapter
 * release fence; the original ndo_open module pin is still held. */
static inline int wr_iot_aux_close_recovery_queue(
 struct wr_iot_aux_close_recovery *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 int netdev_held,int adapter_release_fenced){
 if(!owner||!record||!radio||owner->phase!=WR_RECOVERY_IDLE||
    owner->stop_requested||!netdev_held||!adapter_release_fenced||
    !record->device||!record->generation||!record->close_serial||
    record->family!=WR_REF_FAMILY_WDS||
    record->phase!=WR_REF_CLOSING||
    (record->close_stage!=1&&record->close_stage!=4)||
    radio->busy!=WR_RADIO_AUX_CLOSE||
    radio->serial!=record->close_serial)return 0;
 owner->device=record->device;owner->generation=record->generation;
 owner->family=record->family;
 owner->serial=record->close_serial;owner->attempts=0;
 owner->deferred_owners=1;owner->completed=0;
 owner->phase=WR_RECOVERY_QUEUED;
 return 1;
}
static inline int wr_iot_aux_close_recovery_begin(
 struct wr_iot_aux_close_recovery *owner){
 if(!owner||owner->phase!=WR_RECOVERY_QUEUED||owner->stop_requested||
    owner->completed||
    !owner->deferred_owners)return 0;
 owner->phase=WR_RECOVERY_RUNNING;owner->attempts++;return 1;
}
/* The worker never retries dev_close: Linux marks a netdev DOWN after the
 * first ndo_stop even if that callback reports an error. Route only the
 * original ticket to its retained direct continuation. */
static inline enum wr_iot_recovery_action wr_iot_aux_close_recovery_action(
 const struct wr_iot_aux_close_recovery *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio){
 if(!owner||!record||!radio||owner->phase!=WR_RECOVERY_RUNNING||
    !owner->deferred_owners||owner->completed||owner->stop_requested||
    record->device!=owner->device||record->generation!=owner->generation||
    owner->family!=WR_REF_FAMILY_WDS||record->family!=owner->family||
    record->close_serial!=owner->serial||record->phase!=WR_REF_CLOSING||
    radio->busy!=WR_RADIO_AUX_CLOSE||radio->serial!=owner->serial)
  return WR_RECOVERY_NO_ACTION;
 if(record->close_stage==1)return WR_RECOVERY_RETRY_DOWN;
 if(record->close_stage==4)return WR_RECOVERY_COMPLETE_AFTER_DOWN;
 return WR_RECOVERY_NO_ACTION;
}
/* A failed continuation retains the netdev reference, module pin and
 * adapter release fence. Requeue requires an explicit later decision. */
static inline int wr_iot_aux_close_recovery_retain(
 struct wr_iot_aux_close_recovery *owner){
 if(!owner||owner->phase!=WR_RECOVERY_RUNNING||owner->completed||
    !owner->deferred_owners)return 0;
 owner->phase=owner->stop_requested?WR_RECOVERY_STOPPING:WR_RECOVERY_RETAINED;
 return 1;
}
static inline int wr_iot_aux_close_recovery_requeue(
 struct wr_iot_aux_close_recovery *owner,unsigned int max_attempts){
 if(!owner||owner->phase!=WR_RECOVERY_RETAINED||owner->stop_requested||
    owner->completed||
    !owner->deferred_owners||owner->attempts>=max_attempts)return 0;
 owner->phase=WR_RECOVERY_QUEUED;return 1;
}
/* Removal requests stop and must cancel/join real work outside the lock.
 * No adapter/netdev/module resource may be freed just because work stopped. */
static inline int wr_iot_aux_close_recovery_request_stop(
 struct wr_iot_aux_close_recovery *owner){
 if(!owner||owner->phase==WR_RECOVERY_IDLE)return 0;
 owner->stop_requested=1;
 if(owner->phase==WR_RECOVERY_QUEUED||owner->phase==WR_RECOVERY_RETAINED)
  owner->phase=WR_RECOVERY_STOPPING;
 return 1;
}
/* Record checked completion under the same adapter lock as ticket retirement.
 * A later unrelated ticket may update radio.retired_serial before work join. */
static inline int wr_iot_aux_close_recovery_mark_completed(
 struct wr_iot_aux_close_recovery *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio){
 if(!owner||!record||!radio||owner->completed||
    (owner->phase!=WR_RECOVERY_RUNNING&&
     owner->phase!=WR_RECOVERY_STOPPING)||!owner->deferred_owners||
    record->device!=owner->device||record->generation!=owner->generation||
    owner->family!=WR_REF_FAMILY_WDS||record->family!=owner->family||
    record->close_serial!=owner->serial||record->phase!=WR_REF_IDLE||
    record->close_stage!=2||radio->busy==WR_RADIO_AUX_CLOSE||
    radio->retired_serial!=owner->serial)return 0;
 owner->completed=1;return 1;
}
/* Only a joined worker with a recorded completion may dev_put and drop the
 * adapter deferred-owner count. The checked close path drops the module pin. */
static inline int wr_iot_aux_close_recovery_complete(
 struct wr_iot_aux_close_recovery *owner,int work_joined){
 if(!owner||!work_joined||!owner->completed||
    !owner->deferred_owners)return 0;
 wr_iot_aux_close_recovery_init(owner);return 1;
}
#endif
