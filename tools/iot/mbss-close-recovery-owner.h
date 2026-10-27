/* Host contract for an adapter-pinned MBSS recovery continuation.
 * No work_struct, dev_hold or PCI remove binding is installed by this file.
 * All helpers run under the same adapter transition lock as the registry. */
#ifndef WR_IOT_MBSS_CLOSE_RECOVERY_OWNER_H
#define WR_IOT_MBSS_CLOSE_RECOVERY_OWNER_H
#include "interface-registry.h"
#include "radio-transition.h"

enum wr_iot_mbss_recovery_source {
 WR_MBSS_RECOVERY_OPEN_ACQUIRED,
 WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,
 WR_MBSS_RECOVERY_UNCERTAIN
};
enum wr_iot_mbss_recovery_action {
 WR_MBSS_RECOVERY_NONE,
 WR_MBSS_RECOVERY_BEGIN_CLOSE,
 WR_MBSS_RECOVERY_CONTINUE_CLOSE,
 WR_MBSS_RECOVERY_RECONCILE
};
enum wr_iot_mbss_recovery_phase {
 WR_MBSS_OWNER_IDLE, WR_MBSS_OWNER_QUEUED, WR_MBSS_OWNER_RUNNING,
 WR_MBSS_OWNER_RETAINED, WR_MBSS_OWNER_STOPPING
};
struct wr_iot_mbss_recovery_owner {
 const void *device;
 unsigned long generation,open_token,close_serial;
 struct wr_iot_radio_ticket close_ticket;
 int close_ticket_valid;
 enum wr_iot_mbss_recovery_source source;
 enum wr_iot_mbss_recovery_phase phase;
 unsigned int deferred_owners,attempts;
 int stop_requested,completed;
};
/* Main-down, reset or PCI retire may advance the epoch after a close ticket
 * was admitted. Match the original ticket and honor the same invalidation
 * allowance as wr_iot_radio_finish; never synthesize a new ticket. */
static inline int wr_iot_mbss_recovery_ticket_current(
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_radio_ticket *ticket){
 return radio&&ticket&&ticket->serial==radio->serial&&
  ticket->operation==radio->busy&&
  (ticket->epoch==radio->epoch||radio->phase==WR_RADIO_CLOSING||
   radio->main_inhibited||radio->reset_pending);
}
static inline int wr_iot_mbss_recovery_ticket_recorded(
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_ticket *ticket){
 return record&&ticket&&!ticket->reset_kind&&
  record->close_epoch&&record->close_vendor_count&&
  ((ticket->operation==WR_RADIO_CLOSE&&
    record->close_vendor_count==1U)||
   (ticket->operation==WR_RADIO_BSS_CLOSE&&
    record->close_vendor_count>1U))&&
  record->close_epoch==ticket->epoch&&
  record->close_prior_phase==(int)ticket->prior_phase&&
  record->close_prior_ready==ticket->prior_ready;
}
static inline void wr_iot_mbss_recovery_init(
 struct wr_iot_mbss_recovery_owner *owner){
 owner->device=0;owner->generation=0;owner->open_token=0;
 owner->close_serial=0;owner->source=WR_MBSS_RECOVERY_UNCERTAIN;
 owner->close_ticket_valid=0;
 owner->phase=WR_MBSS_OWNER_IDLE;owner->deferred_owners=0;
 owner->attempts=0;owner->stop_requested=0;owner->completed=0;
}
/* The caller must already hold a netdev ref and prevent adapter release.
 * An OPEN_ACQUIRED record includes the vendor count acquired before a later
 * failure such as CR_ENABLE or a refused close admission. It may be queued
 * while another radio operation owns the ticket; action waits for that
 * operation to clear. It cannot await ndo_stop after failed ndo_open. */
static inline int wr_iot_mbss_recovery_queue(
 struct wr_iot_mbss_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 enum wr_iot_mbss_recovery_source source,
 const struct wr_iot_radio_ticket *ticket,
 int netdev_held,int adapter_release_fenced){
 if(!owner||!record||!radio||owner->phase!=WR_MBSS_OWNER_IDLE||
    !netdev_held||!adapter_release_fenced||!record->device||
    !record->generation||!record->last_token||!record->published||
    record->family!=WR_REF_FAMILY_MBSS)return 0;
 if(source==WR_MBSS_RECOVERY_OPEN_ACQUIRED){
  if(record->phase!=WR_REF_OWNED||ticket)return 0;
 }else if(source==WR_MBSS_RECOVERY_CLOSE_INCOMPLETE){
  if(record->phase!=WR_REF_CLOSING||!record->close_serial||
     (record->close_stage!=2&&record->close_stage!=3)||
     (radio->busy!=WR_RADIO_BSS_CLOSE&&radio->busy!=WR_RADIO_CLOSE)||
     radio->serial!=record->close_serial||!ticket||
     ticket->serial!=record->close_serial||
     !wr_iot_mbss_recovery_ticket_recorded(record,ticket)||
     !wr_iot_mbss_recovery_ticket_current(radio,ticket))return 0;
 }else if(source==WR_MBSS_RECOVERY_UNCERTAIN){
  if(record->phase!=WR_REF_UNCERTAIN_OPEN&&
     !(record->phase==WR_REF_CLOSING&&record->close_stage==5))return 0;
  if(record->phase==WR_REF_CLOSING){
   if(!ticket||!record->close_serial||
      ticket->serial!=record->close_serial||
      !wr_iot_mbss_recovery_ticket_recorded(record,ticket)||
      !wr_iot_mbss_recovery_ticket_current(radio,ticket))return 0;
  }else if(ticket)return 0;
 }else return 0;
 owner->device=record->device;owner->generation=record->generation;
 owner->open_token=record->last_token;
 owner->close_serial=ticket?record->close_serial:0;
 if(ticket){owner->close_ticket=*ticket;owner->close_ticket_valid=1;}
 else owner->close_ticket_valid=0;
 owner->source=source;owner->phase=WR_MBSS_OWNER_QUEUED;
 owner->deferred_owners=1;owner->attempts=0;
 owner->stop_requested=0;owner->completed=0;
 return 1;
}
static inline int wr_iot_mbss_recovery_begin(
 struct wr_iot_mbss_recovery_owner *owner){
 if(!owner||owner->phase!=WR_MBSS_OWNER_QUEUED||
    owner->stop_requested||owner->completed||!owner->deferred_owners)return 0;
 owner->phase=WR_MBSS_OWNER_RUNNING;owner->attempts++;return 1;
}
static inline enum wr_iot_mbss_recovery_action wr_iot_mbss_recovery_action(
 const struct wr_iot_mbss_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *slots,unsigned int count,
 unsigned int vendor_count){
 if(!owner||!record||!radio||owner->phase!=WR_MBSS_OWNER_RUNNING||
    owner->stop_requested||owner->completed||!owner->deferred_owners||
    record->device!=owner->device||
    record->generation!=owner->generation||
    record->last_token!=owner->open_token||
    record->family!=WR_REF_FAMILY_MBSS)return WR_MBSS_RECOVERY_NONE;
 if(owner->source==WR_MBSS_RECOVERY_OPEN_ACQUIRED){
  if(record->phase!=WR_REF_OWNED||radio->busy||
     !wr_iot_registry_count_matches(slots,count,vendor_count))
   return WR_MBSS_RECOVERY_NONE;
  return WR_MBSS_RECOVERY_BEGIN_CLOSE;
 }
 if(owner->source==WR_MBSS_RECOVERY_CLOSE_INCOMPLETE){
  if(record->phase!=WR_REF_CLOSING||
     record->close_serial!=owner->close_serial||
     !owner->close_ticket_valid||
     !wr_iot_mbss_recovery_ticket_recorded(record,
                                            &owner->close_ticket)||
     (record->close_stage!=2&&record->close_stage!=3)||
     (radio->busy!=WR_RADIO_BSS_CLOSE&&radio->busy!=WR_RADIO_CLOSE)||
     !wr_iot_mbss_recovery_ticket_current(radio,
                                           &owner->close_ticket))
   return WR_MBSS_RECOVERY_NONE;
  return WR_MBSS_RECOVERY_CONTINUE_CLOSE;
 }
 if(owner->source==WR_MBSS_RECOVERY_UNCERTAIN&&
    (record->phase==WR_REF_UNCERTAIN_OPEN||
     (record->phase==WR_REF_CLOSING&&record->close_stage==5&&
      owner->close_ticket_valid&&
      record->close_serial==owner->close_ticket.serial&&
      wr_iot_mbss_recovery_ticket_recorded(record,
                                            &owner->close_ticket)&&
      wr_iot_mbss_recovery_ticket_current(radio,
                                           &owner->close_ticket))))
  return WR_MBSS_RECOVERY_RECONCILE;
 return WR_MBSS_RECOVERY_NONE;
}
/* Copy under the adapter lock immediately before handing the exact ticket
 * to checked close. The worker must still retain netdev/adapter lifetimes. */
static inline int wr_iot_mbss_recovery_copy_close_ticket(
 const struct wr_iot_mbss_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_interface_ref *slots,unsigned int count,
 unsigned int vendor_count,struct wr_iot_radio_ticket *out){
 if(!out||wr_iot_mbss_recovery_action(owner,record,radio,slots,count,
                                      vendor_count)!=
           WR_MBSS_RECOVERY_CONTINUE_CLOSE)return 0;
 *out=owner->close_ticket;return 1;
}
/* Called after BEGIN_CLOSE successfully claims a ticket, under the lock. */
static inline int wr_iot_mbss_recovery_bind_close(
 struct wr_iot_mbss_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio,
 const struct wr_iot_radio_ticket *ticket){
 if(!owner||!record||!radio||!ticket||
    owner->source!=WR_MBSS_RECOVERY_OPEN_ACQUIRED||
    owner->phase!=WR_MBSS_OWNER_RUNNING||owner->close_serial||
    owner->close_ticket_valid||
    record->device!=owner->device||
    record->generation!=owner->generation||
    record->last_token!=owner->open_token||
    record->phase!=WR_REF_OWNED||
    !wr_iot_mbss_recovery_ticket_recorded(record,ticket)||
    (ticket->operation!=WR_RADIO_BSS_CLOSE&&
     ticket->operation!=WR_RADIO_CLOSE)||
    !ticket->serial||radio->busy!=ticket->operation||
    radio->serial!=ticket->serial||
    radio->epoch!=ticket->epoch)return 0;
 owner->close_serial=ticket->serial;
 owner->close_ticket=*ticket;owner->close_ticket_valid=1;
 owner->source=WR_MBSS_RECOVERY_CLOSE_INCOMPLETE;
 return 1;
}
static inline int wr_iot_mbss_recovery_mark_completed(
 struct wr_iot_mbss_recovery_owner *owner,
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_transition *radio){
 if(!owner||!record||!radio||!owner->close_serial||
    !owner->close_ticket_valid||
    (owner->phase!=WR_MBSS_OWNER_RUNNING&&
     owner->phase!=WR_MBSS_OWNER_STOPPING)||!owner->deferred_owners||
    record->device!=owner->device||
    record->generation!=owner->generation||
    record->last_token!=owner->open_token||
    record->phase!=WR_REF_IDLE||record->close_stage!=4||
    !wr_iot_mbss_recovery_ticket_recorded(record,
                                           &owner->close_ticket)||
    record->close_serial!=owner->close_ticket.serial||radio->busy||
    radio->retired_serial!=owner->close_serial)return 0;
 owner->completed=1;return 1;
}
static inline int wr_iot_mbss_recovery_retain(
 struct wr_iot_mbss_recovery_owner *owner){
 if(!owner||owner->phase!=WR_MBSS_OWNER_RUNNING||
    owner->completed||!owner->deferred_owners)return 0;
 owner->phase=owner->stop_requested?
              WR_MBSS_OWNER_STOPPING:WR_MBSS_OWNER_RETAINED;
 return 1;
}
static inline int wr_iot_mbss_recovery_requeue(
 struct wr_iot_mbss_recovery_owner *owner,unsigned int max_attempts){
 if(!owner||owner->phase!=WR_MBSS_OWNER_RETAINED||
    owner->stop_requested||owner->completed||
    !owner->deferred_owners||owner->attempts>=max_attempts)return 0;
 owner->phase=WR_MBSS_OWNER_QUEUED;return 1;
}
static inline int wr_iot_mbss_recovery_request_stop(
 struct wr_iot_mbss_recovery_owner *owner){
 if(!owner||owner->phase==WR_MBSS_OWNER_IDLE)return 0;
 owner->stop_requested=1;
 if(owner->phase==WR_MBSS_OWNER_QUEUED||
    owner->phase==WR_MBSS_OWNER_RETAINED)
  owner->phase=WR_MBSS_OWNER_STOPPING;
 return 1;
}
/* Only a joined, successful worker may dev_put and drop the adapter fence.
 * The checked close path has already released the original module pin. */
static inline int wr_iot_mbss_recovery_complete(
 struct wr_iot_mbss_recovery_owner *owner,int work_joined){
 if(!owner||!work_joined||!owner->completed||
    !owner->deferred_owners)return 0;
 wr_iot_mbss_recovery_init(owner);return 1;
}
#endif
