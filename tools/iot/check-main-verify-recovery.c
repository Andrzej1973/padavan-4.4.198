/* Host-only transition from a failed main VERIFY to a retained close owner.
 * This does not schedule kernel work, acquire RTNL, or pin a real netdev. */
#include "virtual-open-claim.h"
#include "main-open-recovery-owner.h"
#include <assert.h>
#include <stdio.h>

int main(void)
{
 struct wr_iot_radio_transition radio;
 struct wr_iot_radio_ticket open_ticket, verify_ticket, next;
 struct wr_iot_interface_ref refs[1]={{0}}, *record;
 struct wr_iot_main_recovery_owner owner;
 unsigned long generation=0;
 int main_dev=1;

 wr_iot_radio_transition_init(&radio);
 record=wr_iot_registry_add_family(refs,1,&generation,&main_dev,
                                    WR_REF_FAMILY_MAIN);
 assert(record && record->published==0);
 record->published=1;
 assert(wr_iot_radio_begin(&radio,radio.epoch,WR_RADIO_START,&open_ticket));
 assert(wr_iot_ref_reserve(record,&main_dev,generation,open_ticket.serial));
 assert(wr_iot_ref_open_finish(record,&main_dev,generation,open_ticket.serial,1));
 assert(wr_iot_radio_finish_unverified(&radio,&open_ticket));
 assert(wr_iot_radio_begin(&radio,radio.epoch,WR_RADIO_VERIFY,&verify_ticket));
 assert(!wr_iot_main_radio_verify_owned(&radio,refs,1,&main_dev,1,
                                        &verify_ticket,0));
 assert(!radio.busy && !radio.main_ready);
 assert(!wr_iot_radio_begin(&radio,radio.epoch,WR_RADIO_BSS_OPEN,&next));
 assert(record->phase==WR_REF_OWNED && record->last_token==open_ticket.serial);

 wr_iot_main_recovery_init(&owner);
 assert(!wr_iot_main_recovery_queue(&owner,&radio,record,
   WR_MAIN_RECOVERY_OPEN_ACQUIRED,0,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_queue(&owner,&radio,record,
   WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,0,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_queue(&owner,&radio,record,
   WR_MAIN_RECOVERY_OPEN_ACQUIRED,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(owner.device==&main_dev && owner.generation==generation &&
        owner.open_token==open_ticket.serial && owner.deferred_owners==1);
 assert(!wr_iot_main_recovery_schedule_result(&owner,0));
 assert(owner.phase==WR_MAIN_OWNER_RETAINED && owner.deferred_owners==1);
 assert(record->phase==WR_REF_OWNED && !owner.module_pin_released);
 assert(!wr_iot_main_recovery_begin(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,2,0));
 assert(wr_iot_main_recovery_requeue(&owner,2,1));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 /* PCI retirement may arrive after the recovery retry was queued. It must
  * fence new opens without stopping this exact checked close first. */
 wr_iot_radio_retire(&radio);
 assert(radio.retiring && !owner.stop_requested);
 assert(wr_iot_main_recovery_begin(&owner));
 assert(wr_iot_main_recovery_action(&owner,record,&radio,refs,1,1)==
        WR_MAIN_RECOVERY_BEGIN_CLOSE);
 /* The worker's proposed action must also be admitted by the real shared
  * main-stop gate after VERIFY has moved the radio to FAULT. */
 assert(radio.phase==WR_RADIO_FAULT);
 {struct wr_iot_radio_ticket close_ticket;
  unsigned long wait_serial=0;
  assert(wr_iot_main_stop_request(&radio,refs,1,&main_dev,&main_dev,1,
          &close_ticket,&wait_serial)==WR_MAIN_STOP_ADMITTED);
  assert(close_ticket.operation==WR_RADIO_CLOSE &&
         radio.phase==WR_RADIO_CLOSING && !radio.main_ready);
 }
 puts("PASS failed main VERIFY retains owner across rejected scheduling; queued close survives PCI retirement before stop");
 return 0;
}
