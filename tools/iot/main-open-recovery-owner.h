/* Host-only contract for recovery after a failed main ndo_open.
 * This does not bind a workqueue, RTNL path, driver callback, or PCI owner. */
#ifndef WR_IOT_MAIN_OPEN_RECOVERY_OWNER_H
#define WR_IOT_MAIN_OPEN_RECOVERY_OWNER_H
#include "main-stop-owned.h"

enum wr_iot_main_recovery_source {
 WR_MAIN_RECOVERY_OPEN_ACQUIRED,
 WR_MAIN_RECOVERY_CLOSE_INCOMPLETE,
 WR_MAIN_RECOVERY_CLOSE_UNCERTAIN,
 WR_MAIN_RECOVERY_UNCERTAIN
};
enum wr_iot_main_recovery_queue_origin {
 WR_MAIN_QUEUE_NORMAL, WR_MAIN_QUEUE_RETIREMENT_CLOSE
};
enum wr_iot_main_recovery_action {
 WR_MAIN_RECOVERY_NONE,
 WR_MAIN_RECOVERY_BEGIN_CLOSE,
 WR_MAIN_RECOVERY_CONTINUE_CLOSE,
 WR_MAIN_RECOVERY_RECONCILE
};
enum wr_iot_main_recovery_phase {
 WR_MAIN_OWNER_IDLE, WR_MAIN_OWNER_QUEUED, WR_MAIN_OWNER_RUNNING,
 WR_MAIN_OWNER_RETAINED, WR_MAIN_OWNER_STOPPING
};
struct wr_iot_main_recovery_owner {
 const void *device;
 unsigned long generation,open_token,close_serial;
 struct wr_iot_radio_ticket close_ticket;
 enum wr_iot_main_recovery_source source;
 enum wr_iot_main_recovery_phase phase;
 unsigned int deferred_owners,attempts,failed_submissions;
 int close_ticket_valid,stop_requested,completed,module_pin_released;
 int schedule_recorded;
};
static inline void wr_iot_main_recovery_init(
 struct wr_iot_main_recovery_owner *owner){
 owner->device=0;owner->generation=0;owner->open_token=0;
 owner->close_serial=0;owner->source=WR_MAIN_RECOVERY_UNCERTAIN;
 owner->phase=WR_MAIN_OWNER_IDLE;owner->deferred_owners=0;owner->attempts=0;
 owner->failed_submissions=0;owner->schedule_recorded=0;
 owner->close_ticket_valid=0;owner->stop_requested=0;owner->completed=0;
 owner->module_pin_released=0;
}
static inline int wr_iot_main_recovery_ticket_recorded(
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_ticket *ticket){
 return record&&ticket&&!ticket->reset_kind&&record->close_epoch&&
  record->close_vendor_count&&
  ((ticket->operation==WR_RADIO_CLOSE&&record->close_vendor_count==1U)||
   (ticket->operation==WR_RADIO_BSS_CLOSE&&record->close_vendor_count>1U))&&
  record->close_epoch==ticket->epoch&&
  record->close_prior_phase==(int)ticket->prior_phase&&
  record->close_prior_ready==ticket->prior_ready;
}
static inline int wr_iot_main_recovery_ticket_current(
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_radio_ticket *ticket){
 return radio&&ticket&&radio->serial==ticket->serial&&
  radio->busy==ticket->operation&&
  (radio->epoch==ticket->epoch||radio->phase==WR_RADIO_CLOSING||
   radio->main_inhibited||radio->reset_pending);
}
/* While the exact close ticket is held, its owner is CLOSING rather than
 * OWNED. Count that one recorded reference; reject any other ambiguous slot. */
static inline int wr_iot_main_recovery_close_count_matches(
 const struct wr_iot_interface_ref *slots,unsigned int count,
 const struct wr_iot_interface_ref *closing,unsigned int vendor_count){
 return wr_iot_main_close_registry_matches(slots,count,closing,vendor_count);
}
/* Registry ownership records the count BEFORE checked DOWN. The actual
 * vendor count drops by one at virtual_down_stage 1 (last close) or 2
 * (completed virtual DOWN). Do not reject the retained exact ticket merely
 * because the physical close failed after this decrement. */
static inline int wr_iot_main_recovery_vendor_count_matches(
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_ticket *ticket,unsigned int vendor_count){
 unsigned int prior,stage;
 if(!radio||!record||!ticket||!record->close_vendor_count)return 0;
 prior=record->close_vendor_count;stage=radio->virtual_down_stage;
 if(stage==0U)return vendor_count==prior;
 if(stage==1U)return ticket->operation==WR_RADIO_CLOSE&&prior==1U&&
                     vendor_count==0U;
 if(stage==2U)return prior>0U&&vendor_count==prior-1U;
 return 0;
}
/* Caller already holds a netdev reference and adapter-release fence, and
 * holds the shared adapter lock while checking retiring and queueing work.
 * During retirement only the PCI removal owner may enqueue an acquired-main
 * close; ordinary recovery and uncertain-open reconciliation stay blocked.
 * The main-open module pin remains until checked close releases it. */
static inline int wr_iot_main_recovery_queue(
 struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *record,
 enum wr_iot_main_recovery_source source,int netdev_held,
 int adapter_release_fenced,
 enum wr_iot_main_recovery_queue_origin origin,
 int retirement_owner_active){
 if(!owner||!radio||!record||
    owner->phase!=WR_MAIN_OWNER_IDLE||!netdev_held||
    !adapter_release_fenced||!record->device||!record->generation||
    !record->last_token||!record->published||record->removing||
    record->family!=WR_REF_FAMILY_MAIN)return 0;
 if(origin==WR_MAIN_QUEUE_NORMAL){
  if(radio->retiring||retirement_owner_active)return 0;
 }else if(origin==WR_MAIN_QUEUE_RETIREMENT_CLOSE){
  if(!radio->retiring||!retirement_owner_active||
     source!=WR_MAIN_RECOVERY_OPEN_ACQUIRED)return 0;
 }else return 0;
 if(source==WR_MAIN_RECOVERY_OPEN_ACQUIRED){
  if(record->phase!=WR_REF_OWNED||record->open_unmutated)return 0;
 }else if(source==WR_MAIN_RECOVERY_UNCERTAIN){
  if(record->phase!=WR_REF_UNCERTAIN_OPEN||record->open_unmutated)return 0;
 }else return 0;
 owner->device=record->device;owner->generation=record->generation;
 owner->open_token=record->last_token;owner->source=source;
 owner->phase=WR_MAIN_OWNER_QUEUED;owner->deferred_owners=1;
 owner->attempts=0;owner->failed_submissions=0;
 owner->schedule_recorded=0;owner->stop_requested=0;owner->completed=0;
 owner->module_pin_released=0;owner->close_serial=0;
 owner->close_ticket_valid=0;return 1;
}
/* Failed ndo_stop may leave a recorded CLOSING reference after the void
 * vendor preclose. Stage 1 is ambiguous and may only be reconciled, never
 * replayed. Stages 2/3 may resume the exact checked DOWN ticket. The caller
 * pins netdev/adapter and holds the shared transition lock while queueing. */
static inline int wr_iot_main_recovery_queue_close(
 struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_interface_ref *slots,unsigned int count,
 const struct wr_iot_radio_ticket *ticket,unsigned int vendor_count,
 int netdev_held,int adapter_release_fenced,
 enum wr_iot_main_recovery_queue_origin origin,
 int retirement_owner_active){
 if(!owner||!radio||!record||!slots||!ticket||
    owner->phase!=WR_MAIN_OWNER_IDLE||!netdev_held||
    !adapter_release_fenced||!record->device||!record->generation||
    !record->last_token||!record->published||record->removing||
    record->family!=WR_REF_FAMILY_MAIN||record->phase!=WR_REF_CLOSING||
    record->close_serial!=ticket->serial||
    (record->close_stage!=1U&&record->close_stage!=2U&&
     record->close_stage!=3U)||
    !wr_iot_main_recovery_ticket_recorded(record,ticket)||
    !wr_iot_main_recovery_ticket_current(radio,ticket)||
    !wr_iot_main_recovery_vendor_count_matches(radio,record,ticket,
                                                vendor_count)||
    !wr_iot_main_recovery_close_count_matches(slots,count,record,
                                               record->close_vendor_count))return 0;
 if(origin==WR_MAIN_QUEUE_NORMAL){
  if(radio->retiring||retirement_owner_active)return 0;
 }else if(origin==WR_MAIN_QUEUE_RETIREMENT_CLOSE){
  if(!radio->retiring||!retirement_owner_active)return 0;
 }else return 0;
 owner->device=record->device;owner->generation=record->generation;
 owner->open_token=record->last_token;owner->close_serial=ticket->serial;
 owner->close_ticket=*ticket;owner->close_ticket_valid=1;
 owner->source=record->close_stage==1U?
  WR_MAIN_RECOVERY_CLOSE_UNCERTAIN:WR_MAIN_RECOVERY_CLOSE_INCOMPLETE;
 owner->phase=WR_MAIN_OWNER_QUEUED;owner->deferred_owners=1;
 owner->attempts=0;owner->failed_submissions=0;
 owner->schedule_recorded=0;owner->stop_requested=0;owner->completed=0;
 owner->module_pin_released=0;return 1;
}
static inline int wr_iot_main_recovery_begin(
 struct wr_iot_main_recovery_owner *owner){
 if(!owner||owner->phase!=WR_MAIN_OWNER_QUEUED||owner->stop_requested||
    owner->completed||!owner->deferred_owners||!owner->schedule_recorded)return 0;
 owner->phase=WR_MAIN_OWNER_RUNNING;owner->attempts++;return 1;
}
/* Call immediately after schedule_work while holding the same adapter lock
 * that admitted the owner. A rejected enqueue retains all pins and the exact
 * ticket; it is not evidence that the recovery callback ran. The caller must
 * join any previous work before a bounded requeue. */
static inline int wr_iot_main_recovery_schedule_result(
 struct wr_iot_main_recovery_owner *owner,int accepted){
 if(!owner||owner->phase!=WR_MAIN_OWNER_QUEUED||!owner->deferred_owners||
    owner->schedule_recorded)
  return 0;
 owner->schedule_recorded=1;
 if(accepted)return 1;
 owner->failed_submissions++;
 owner->phase=WR_MAIN_OWNER_RETAINED;
 return 0;
}
/* A callback that cannot take RTNL must not block a cancel_work_sync join.
 * No hardware action began, so retain the same owner without spending an
 * execution attempt. An external owner may retry only after joining work. */
static inline int wr_iot_main_recovery_rtnl_unavailable(
 struct wr_iot_main_recovery_owner *owner){
 if(!owner||owner->phase!=WR_MAIN_OWNER_QUEUED||
    !owner->schedule_recorded||!owner->deferred_owners||
    owner->completed||owner->stop_requested)return 0;
 owner->phase=WR_MAIN_OWNER_RETAINED;return 1;
}
/* The external reaper may cancel a queued item before its callback starts.
 * cancel_work_sync returning true proves the pending submission was canceled;
 * after the join, the same owner can be considered for a bounded retry. */
static inline int wr_iot_main_recovery_canceled_before_run(
 struct wr_iot_main_recovery_owner *owner,int pending_canceled){
 if(!owner||!pending_canceled||owner->phase!=WR_MAIN_OWNER_QUEUED||
    !owner->schedule_recorded||!owner->deferred_owners||
    owner->completed||owner->stop_requested)return 0;
 owner->phase=WR_MAIN_OWNER_RETAINED;return 1;
}
static inline enum wr_iot_main_recovery_action wr_iot_main_recovery_action(
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *slots,unsigned int count,
 unsigned int vendor_count){
 if(!owner||!record||!radio||owner->phase!=WR_MAIN_OWNER_RUNNING||
    owner->stop_requested||owner->completed||!owner->deferred_owners||
    record->device!=owner->device||record->generation!=owner->generation||
    record->last_token!=owner->open_token||
    record->family!=WR_REF_FAMILY_MAIN)return WR_MAIN_RECOVERY_NONE;
 if(owner->source==WR_MAIN_RECOVERY_OPEN_ACQUIRED){
  if(record->phase!=WR_REF_OWNED||radio->busy||
     !wr_iot_registry_count_matches(slots,count,vendor_count))
   return WR_MAIN_RECOVERY_NONE;
  return WR_MAIN_RECOVERY_BEGIN_CLOSE;
 }
 if(owner->source==WR_MAIN_RECOVERY_CLOSE_INCOMPLETE){
  if(record->phase!=WR_REF_CLOSING||
     record->close_serial!=owner->close_serial||
     !owner->close_ticket_valid||
     !wr_iot_main_recovery_ticket_recorded(record,&owner->close_ticket)||
     (record->close_stage!=2U&&record->close_stage!=3U)||
     !wr_iot_main_recovery_vendor_count_matches(radio,record,
                                                 &owner->close_ticket,
                                                 vendor_count)||
     !wr_iot_main_recovery_close_count_matches(slots,count,record,
                                                record->close_vendor_count)||
     !wr_iot_main_recovery_ticket_current(radio,&owner->close_ticket))
   return WR_MAIN_RECOVERY_NONE;
  return WR_MAIN_RECOVERY_CONTINUE_CLOSE;
 }
 if(owner->source==WR_MAIN_RECOVERY_CLOSE_UNCERTAIN&&
    record->phase==WR_REF_CLOSING&&record->close_stage==1U&&
    owner->close_ticket_valid&&
    record->close_serial==owner->close_serial&&
    wr_iot_main_recovery_ticket_recorded(record,&owner->close_ticket)&&
    wr_iot_main_recovery_vendor_count_matches(radio,record,
                                                &owner->close_ticket,
                                                vendor_count)&&
    wr_iot_main_recovery_close_count_matches(slots,count,record,
                                               record->close_vendor_count)&&
    wr_iot_main_recovery_ticket_current(radio,&owner->close_ticket))
  return WR_MAIN_RECOVERY_RECONCILE;
 /* Uncertain open does not prove whether VIRTUAL_IF_UP incremented the
  * vendor count. Never guess a DOWN/decrement; keep ownership for reconciliation. */
 if(owner->source==WR_MAIN_RECOVERY_UNCERTAIN&&
    record->phase==WR_REF_UNCERTAIN_OPEN)return WR_MAIN_RECOVERY_RECONCILE;
 return WR_MAIN_RECOVERY_NONE;
}
static inline int wr_iot_main_recovery_bind_close(
 struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_radio_ticket *ticket){
 if(!owner||!record||!radio||!ticket||
    owner->source!=WR_MAIN_RECOVERY_OPEN_ACQUIRED||
    owner->phase!=WR_MAIN_OWNER_RUNNING||owner->close_ticket_valid||
    record->device!=owner->device||record->generation!=owner->generation||
    record->last_token!=owner->open_token||record->phase!=WR_REF_CLOSING||
    (ticket->operation!=WR_RADIO_CLOSE&&
     ticket->operation!=WR_RADIO_BSS_CLOSE)||!ticket->serial||
    record->close_serial!=ticket->serial||
    !wr_iot_main_recovery_ticket_recorded(record,ticket)||
    !wr_iot_main_recovery_ticket_current(radio,ticket))return 0;
 owner->close_serial=ticket->serial;owner->close_ticket=*ticket;
 owner->close_ticket_valid=1;owner->source=WR_MAIN_RECOVERY_CLOSE_INCOMPLETE;
 return 1;
}
/* A stage-1 preclose did not produce its returned milestone. Even if the
 * caller cannot prove whether the void call began, keep the exact ticket for
 * reconciliation and never replay RTMPInfClose. Shared lock required. */
static inline int wr_iot_main_recovery_preclose_uncertain(
 struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_interface_ref *record){
 if(!owner||!record||owner->phase!=WR_MAIN_OWNER_RUNNING||
    owner->source!=WR_MAIN_RECOVERY_CLOSE_INCOMPLETE||
    !owner->close_ticket_valid||record->phase!=WR_REF_CLOSING||
    record->close_stage!=1U||
    record->close_serial!=owner->close_serial||
    !wr_iot_main_recovery_ticket_recorded(record,&owner->close_ticket))return 0;
 owner->source=WR_MAIN_RECOVERY_CLOSE_UNCERTAIN;return 1;
}
static inline int wr_iot_main_recovery_copy_close_ticket(
 const struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *slots,unsigned int count,
 unsigned int vendor_count,struct wr_iot_radio_ticket *out){
 if(!out||wr_iot_main_recovery_action(owner,record,radio,slots,count,
      vendor_count)!=WR_MAIN_RECOVERY_CONTINUE_CLOSE)return 0;
 *out=owner->close_ticket;return 1;
}
/* Accept only the durable exact-record receipt written after checked DOWN and
 * ticket retirement; this does not itself prove hardware or callback safety. */
static inline int wr_iot_main_recovery_mark_completed(
 struct wr_iot_main_recovery_owner *owner,
 const struct wr_iot_interface_ref *record){
 if(!owner||!record||!owner->close_ticket_valid||!owner->close_serial||
    (owner->phase!=WR_MAIN_OWNER_RUNNING&&
     owner->phase!=WR_MAIN_OWNER_STOPPING)||!owner->deferred_owners||
    record->device!=owner->device||record->generation!=owner->generation||
    record->last_token!=owner->open_token||record->phase!=WR_REF_IDLE||
    record->close_stage!=4U||record->close_serial!=owner->close_serial||
    !wr_iot_main_recovery_ticket_recorded(record,&owner->close_ticket))return 0;
 owner->completed=1;return 1;
}
/* The running callback may release the acquired open pin only after checked
 * close completion. It cannot wait for its own work item to be joined; the
 * external remove owner joins it before resetting this record/freeing memory.
 * released is caller proof of the actual module decrement, not the decrement. */
static inline int wr_iot_main_recovery_mark_module_pin_released(
 struct wr_iot_main_recovery_owner *owner,int owner_execution_active,
 int released){
 if(!owner||(owner->phase!=WR_MAIN_OWNER_RUNNING&&
             owner->phase!=WR_MAIN_OWNER_STOPPING)||!owner->completed||
    !owner_execution_active||!released||owner->module_pin_released)return 0;
 owner->module_pin_released=1;return 1;
}
static inline int wr_iot_main_recovery_retain(
 struct wr_iot_main_recovery_owner *owner){
 if(!owner||owner->phase!=WR_MAIN_OWNER_RUNNING||owner->completed||
    !owner->deferred_owners)return 0;
 owner->phase=owner->stop_requested?WR_MAIN_OWNER_STOPPING:
              WR_MAIN_OWNER_RETAINED;return 1;
}
/* A retained owner can make another bounded attempt only after the prior
 * kernel work callback has returned and an external owner has joined it.
 * Reusing a still-running work_struct may make schedule_work reject the
 * retry while this state machine incorrectly reports QUEUED. Never retry an
 * uncertain open as a speculative close. */
static inline int wr_iot_main_recovery_requeue(
 struct wr_iot_main_recovery_owner *owner,unsigned int max_attempts,
 int previous_work_joined){
 if(!owner||owner->phase!=WR_MAIN_OWNER_RETAINED||owner->stop_requested||
    owner->completed||!owner->deferred_owners||!previous_work_joined||
    (owner->source==WR_MAIN_RECOVERY_UNCERTAIN||
     owner->source==WR_MAIN_RECOVERY_CLOSE_UNCERTAIN)||
    owner->attempts>=max_attempts||
    owner->failed_submissions>=max_attempts-owner->attempts)return 0;
 owner->phase=WR_MAIN_OWNER_QUEUED;owner->schedule_recorded=0;return 1;
}
/* PCI removal requests stop before joining the actual worker outside the
 * adapter lock. A stopped but incomplete owner still fences adapter free. */
static inline int wr_iot_main_recovery_request_stop(
 struct wr_iot_main_recovery_owner *owner){
 if(!owner||owner->phase==WR_MAIN_OWNER_IDLE)return 0;
 owner->stop_requested=1;
 if(owner->phase==WR_MAIN_OWNER_QUEUED||
    owner->phase==WR_MAIN_OWNER_RETAINED)
  owner->phase=WR_MAIN_OWNER_STOPPING;
 return 1;
}
static inline int wr_iot_main_recovery_complete(
 struct wr_iot_main_recovery_owner *owner,int work_joined){
 if(!owner||!work_joined||!owner->completed||!owner->module_pin_released||
    !owner->deferred_owners)return 0;
 wr_iot_main_recovery_init(owner);return 1;
}
#endif
