/* Candidate main-stop admission. Caller holds the ONE adapter lock over
 * registry, vendor count and transition state, with main netdev pinned.
 * This gate remains closed until all five UP/DOWN caller families record
 * their references through the shared registry. */
#ifndef WR_IOT_MAIN_STOP_OWNED_H
#define WR_IOT_MAIN_STOP_OWNED_H
#include "interface-registry.h"
#include "radio-transition.h"
enum wr_iot_main_stop_result {
 WR_MAIN_STOP_INVALID,
 WR_MAIN_STOP_WAIT_TICKET,
 WR_MAIN_STOP_NEEDS_RECOVERY,
 WR_MAIN_STOP_ADMITTED
};
/* ndo_stop runs under RTNL and its return is ignored in Linux 4.4.
 * WAIT_TICKET is a handoff to an adapter-pinned owner after ndo_stop, never
 * permission to wait on RTNL or to free the module pin in this callback. */
static inline enum wr_iot_main_stop_result wr_iot_main_stop_request(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int slot_count,
 const void *main_device,const void *closing_device,unsigned int vendor_count,
 struct wr_iot_radio_ticket *ticket,unsigned long *wait_serial){
 if(!radio||!main_device||main_device!=closing_device||!ticket||!vendor_count||
    !wait_serial||!wr_iot_registry_find_owned(slots,slot_count,main_device))
  return WR_MAIN_STOP_INVALID;
 *wait_serial=0;
 /* Once the main owner is known, a close request must invalidate an
  * in-flight secondary open even when its RESERVED record makes the count
  * temporarily unmatched. A separate owner waits and recounts after ndo_stop. */
 if(!radio->main_inhibited)wr_iot_radio_main_down(radio);
 if(!wr_iot_registry_count_matches(slots,slot_count,vendor_count))
  goto deferred;
 if(wr_iot_radio_begin_main_stop(radio,vendor_count,ticket))
  return WR_MAIN_STOP_ADMITTED;
deferred:
 if(radio->busy){*wait_serial=radio->serial;return WR_MAIN_STOP_WAIT_TICKET;}
 return WR_MAIN_STOP_NEEDS_RECOVERY;
}
static inline int wr_iot_main_stop_owned(
 struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *slots,unsigned int slot_count,
 const void *main_device,const void *closing_device,unsigned int vendor_count,
 struct wr_iot_radio_ticket *ticket){
 unsigned long wait_serial;
 return wr_iot_main_stop_request(radio,slots,slot_count,main_device,
  closing_device,vendor_count,ticket,&wait_serial)==WR_MAIN_STOP_ADMITTED;
}
/* RTMPInfClose returns void but mutates beacon/client/steering state. Record
 * its attempt BEFORE the unlocked call; an interrupted stage 1 is ambiguous
 * and must never be replayed as though no vendor mutation happened. */
static inline int wr_iot_main_close_registry_matches(
 const struct wr_iot_interface_ref *slots,unsigned int slot_count,
 const struct wr_iot_interface_ref *closing,unsigned int vendor_count){
 unsigned int i,active=0;int found=0;
 if(!slots||!closing||!vendor_count)return 0;
 for(i=0;i<slot_count;i++){
  const struct wr_iot_interface_ref *r=&slots[i];
  if(r==closing){
   if(found||r->phase!=WR_REF_CLOSING||!r->device||!r->generation||
      !r->published||r->removing||r->family!=WR_REF_FAMILY_MAIN)return 0;
   found=1;
  }else if(r->phase==WR_REF_IDLE)continue;
  else if(r->phase!=WR_REF_OWNED||!r->device||!r->generation||
          !r->published||r->removing)return 0;
  if(active==~0U)return 0;
  active++;
 }
 return found&&active==vendor_count;
}
static inline int wr_iot_main_close_claim_preclose(
 struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *record,
 const struct wr_iot_interface_ref *slots,unsigned int slot_count,
 const struct wr_iot_radio_ticket *ticket,unsigned int vendor_count){
 if(!radio||!record||!ticket||record->phase!=WR_REF_CLOSING||
    record->close_stage||record->close_serial||ticket->reset_kind||
    radio->busy!=ticket->operation||radio->serial!=ticket->serial||
    !wr_iot_main_close_registry_matches(slots,slot_count,record,vendor_count)||
    !((ticket->operation==WR_RADIO_CLOSE&&vendor_count==1U)||
      (ticket->operation==WR_RADIO_BSS_CLOSE&&vendor_count>1U)))return 0;
 record->close_epoch=ticket->epoch;
 record->close_vendor_count=vendor_count;
 record->close_prior_phase=(int)ticket->prior_phase;
 record->close_prior_ready=ticket->prior_ready;
 record->close_serial=ticket->serial;
 record->close_stage=1U;record->close_running=0U;return 1;
}
static inline int wr_iot_main_close_receipt_matches(
 const struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_ticket *ticket){
 return record&&ticket&&record->phase==WR_REF_CLOSING&&
  record->close_serial==ticket->serial&&record->close_epoch==ticket->epoch&&
  record->close_prior_phase==(int)ticket->prior_phase&&
  record->close_prior_ready==ticket->prior_ready&&!ticket->reset_kind&&
  ((ticket->operation==WR_RADIO_CLOSE&&record->close_vendor_count==1U)||
   (ticket->operation==WR_RADIO_BSS_CLOSE&&record->close_vendor_count>1U));
}
/* Mark the void vendor call as started under the shared lock BEFORE calling
 * it unlocked. An interrupted call remains stage 1 and cannot be replayed. */
static inline int wr_iot_main_close_claim_void_preclose(
 struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_ticket *ticket){
 if(!wr_iot_main_close_receipt_matches(record,ticket)||
    record->close_stage!=1U||record->close_running)return 0;
 record->close_running=1U;return 1;
}
/* A return from the void vendor call is a software milestone, not RF proof. */
static inline int wr_iot_main_close_finish_preclose(
 struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_ticket *ticket){
 if(!wr_iot_main_close_receipt_matches(record,ticket)||
    record->close_stage!=1U||!record->close_running)return 0;
 record->close_stage=2U;record->close_running=0U;return 1;
}
static inline int wr_iot_main_close_note_checked_down(
 struct wr_iot_interface_ref *record,
 const struct wr_iot_radio_ticket *ticket,int checked_down,
 int physical_verified){
 if(!wr_iot_main_close_receipt_matches(record,ticket)||
    record->close_stage!=2U||record->close_running||!checked_down||
    (ticket->operation==WR_RADIO_CLOSE&&!physical_verified))return 0;
 record->close_stage=3U;return 1;
}
/* Linux 4.4 ignores ndo_stop's return and clears IFF_UP. A failed or
 * unverified close therefore retains the main reference and module pin for
 * an explicit recovery owner; returning an errno cannot request a retry.
 * Caller holds the shared adapter lock over ticket, record and count. */
static inline int wr_iot_main_stop_complete(
 struct wr_iot_radio_transition *radio,struct wr_iot_interface_ref *record,
 const void *main_device,unsigned long generation,unsigned long open_token,
 const struct wr_iot_radio_ticket *ticket,int checked_down,
 int physical_verified,int *release_pin){
 int accepted;
 if(!radio||!record||!ticket||!release_pin||
    (ticket->operation!=WR_RADIO_CLOSE&&
     ticket->operation!=WR_RADIO_BSS_CLOSE)||
    !wr_iot_ref_matches(record,main_device,generation,open_token)||
    record->phase!=WR_REF_CLOSING||
    record->close_stage!=3U||record->close_running||
    !wr_iot_main_close_receipt_matches(record,ticket)||
    radio->busy!=ticket->operation||radio->serial!=ticket->serial)return 0;
 *release_pin=0;
 accepted=checked_down&&
  (ticket->operation!=WR_RADIO_CLOSE||physical_verified);
 /* Keep the admitted ticket while the caller still owns a retryable close.
  * Finishing it on failure would make the checked hardware stage impossible
  * to resume with the same ticket and could admit a conflicting writer. */
 if(!accepted)return 0;
 if(!wr_iot_radio_finish(radio,ticket,1))return 0;
 if(!wr_iot_ref_consume(record,main_device,generation,open_token))return 0;
 record->close_stage=4U;
 *release_pin=1;
 return 1;
}
#endif
