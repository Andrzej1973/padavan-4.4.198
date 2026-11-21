#include "main-open-recovery-owner.h"
#include <assert.h>
#include <stdio.h>

static void setup(struct wr_iot_radio_transition *radio,
 struct wr_iot_interface_ref *record,int *device,
 struct wr_iot_radio_ticket *ticket){
 wr_iot_radio_transition_init(radio);
 radio->phase=WR_RADIO_READY;radio->main_ready=1;
 wr_iot_ref_init(record,device,1);record->family=WR_REF_FAMILY_MAIN;
 record->published=1;
 assert(wr_iot_ref_reserve(record,device,1,7));
 assert(wr_iot_ref_open_finish(record,device,1,7,1));
 assert(wr_iot_radio_begin_main_stop(radio,1,ticket));
 assert(wr_iot_ref_begin_close(record,device,1,7));
 assert(wr_iot_main_close_claim_preclose(radio,record,record,1,ticket,1));
 assert(wr_iot_main_close_claim_void_preclose(record,ticket));
}
int main(void){
 struct wr_iot_radio_transition radio;
 struct wr_iot_interface_ref record;
 struct wr_iot_radio_ticket ticket,bad;
 struct wr_iot_main_recovery_owner owner;
 int device=1;
 setup(&radio,&record,&device,&ticket);
 wr_iot_main_recovery_init(&owner);
 bad=ticket;bad.serial++;
 assert(!wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &bad,1,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,0,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(owner.source==WR_MAIN_RECOVERY_CLOSE_UNCERTAIN);
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_begin(&owner));
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,1)==
        WR_MAIN_RECOVERY_RECONCILE);
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,0)==
        WR_MAIN_RECOVERY_NONE);
 radio.virtual_down_stage=1;
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,0)==
        WR_MAIN_RECOVERY_RECONCILE);
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,1)==
        WR_MAIN_RECOVERY_NONE);
 radio.virtual_down_stage=0;
 assert(wr_iot_main_recovery_retain(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,3,1));
 assert(!wr_iot_main_recovery_complete(&owner,1));

 setup(&radio,&record,&device,&ticket);
 assert(wr_iot_main_close_finish_preclose(&record,&ticket));
 wr_iot_main_recovery_init(&owner);
 assert(!wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,2,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(owner.source==WR_MAIN_RECOVERY_CLOSE_INCOMPLETE);
 assert(!wr_iot_main_recovery_schedule_result(&owner,0));
 assert(owner.phase==WR_MAIN_OWNER_RETAINED&&owner.close_ticket_valid);
 assert(owner.close_ticket.serial==ticket.serial);
 assert(!wr_iot_main_recovery_requeue(&owner,2,0));
 assert(wr_iot_main_recovery_requeue(&owner,3,1));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_begin(&owner));
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,1)==
        WR_MAIN_RECOVERY_CONTINUE_CLOSE);
 /* Last checked DOWN already decremented the vendor count before a failed
  * physical shutdown. Keep the same ticket admissible at count zero. */
 radio.virtual_down_stage=1;
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,1)==
        WR_MAIN_RECOVERY_NONE);
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,0)==
        WR_MAIN_RECOVERY_CONTINUE_CLOSE);
 radio.virtual_down_stage=2;
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,0)==
        WR_MAIN_RECOVERY_CONTINUE_CLOSE);
 radio.virtual_down_stage=0;
 assert(wr_iot_main_recovery_retain(&owner));
 assert(!wr_iot_main_recovery_requeue(&owner,2,0));
 assert(wr_iot_main_recovery_requeue(&owner,3,1));
 assert(!wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,1,1,WR_MAIN_QUEUE_NORMAL,0));

 setup(&radio,&record,&device,&ticket);
 assert(wr_iot_main_close_finish_preclose(&record,&ticket));
 wr_iot_main_recovery_init(&owner);
 radio.virtual_down_stage=1;
 assert(!wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,0,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(wr_iot_main_recovery_schedule_result(&owner,1));
 assert(wr_iot_main_recovery_begin(&owner));
 assert(wr_iot_main_recovery_action(&owner,&record,&radio,&record,1,0)==
        WR_MAIN_RECOVERY_CONTINUE_CLOSE);

 setup(&radio,&record,&device,&ticket);
 assert(wr_iot_main_close_finish_preclose(&record,&ticket));
 wr_iot_main_recovery_init(&owner);
 radio.retiring=1;
 assert(!wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,1,1,WR_MAIN_QUEUE_NORMAL,0));
 assert(!wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,1,1,WR_MAIN_QUEUE_RETIREMENT_CLOSE,0));
 assert(wr_iot_main_recovery_queue_close(&owner,&radio,&record,&record,1,
  &ticket,1,1,1,WR_MAIN_QUEUE_RETIREMENT_CLOSE,1));
 /* A selective BSS close has the same one-count decrement at stage 2. */
 record.close_vendor_count=2;
 ticket.operation=WR_RADIO_BSS_CLOSE;
 radio.virtual_down_stage=2;
 assert(wr_iot_main_recovery_vendor_count_matches(&radio,&record,&ticket,1));
 assert(!wr_iot_main_recovery_vendor_count_matches(&radio,&record,&ticket,2));
 radio.virtual_down_stage=1;
 assert(!wr_iot_main_recovery_vendor_count_matches(&radio,&record,&ticket,1));
 puts("PASS main close recovery queue: exact ticket, post-DOWN count, reconcile, retirement owner");
 return 0;
}
