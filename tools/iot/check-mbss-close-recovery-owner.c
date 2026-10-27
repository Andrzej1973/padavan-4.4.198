#include "mbss-close-recovery-owner.h"
#include <assert.h>
#include <string.h>

static void owned(struct wr_iot_interface_ref *r,const void *device,
                  enum wr_iot_ref_family family,unsigned long generation){
 wr_iot_ref_init(r,device,generation);
 r->family=family;r->published=1;
 assert(wr_iot_ref_reserve(r,device,generation,1));
 assert(wr_iot_ref_open_finish(r,device,generation,1,1));
}
static void record_ticket(struct wr_iot_interface_ref *r,
                          const struct wr_iot_radio_ticket *ticket,
                          unsigned int vendor_count){
 r->close_epoch=ticket->epoch;r->close_vendor_count=vendor_count;
 r->close_prior_phase=(int)ticket->prior_phase;
 r->close_prior_ready=ticket->prior_ready;
}
int main(void){
 struct wr_iot_interface_ref refs[2];
 struct wr_iot_radio_transition radio;
 struct wr_iot_radio_ticket ticket,bad,copy;
 struct wr_iot_mbss_recovery_owner owner;
 int main_device,mbss_device;
 memset(refs,0,sizeof(refs));
 wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_FAULT;
 owned(&refs[0],&main_device,WR_REF_FAMILY_MAIN,1);
 owned(&refs[1],&mbss_device,WR_REF_FAMILY_MBSS,2);
 wr_iot_mbss_recovery_init(&owner);
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_OPEN_ACQUIRED,0,0,1));
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_OPEN_ACQUIRED,0,1,0));
 radio.busy=WR_RADIO_AUX_CLOSE;
 assert(wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_OPEN_ACQUIRED,0,1,1));
 assert(!wr_iot_mbss_recovery_complete(&owner,1));
 assert(wr_iot_mbss_recovery_begin(&owner));
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_NONE);
 radio.busy=0;
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,1)==
        WR_MBSS_RECOVERY_NONE);
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_BEGIN_CLOSE);
 assert(wr_iot_radio_begin_stop(&radio,2,&ticket));
 record_ticket(&refs[1],&ticket,2);
 refs[1].close_vendor_count=1;
 assert(!wr_iot_mbss_recovery_bind_close(&owner,&refs[1],&radio,&ticket));
 refs[1].close_vendor_count=2;
 bad=ticket;bad.serial++;
 assert(!wr_iot_mbss_recovery_bind_close(&owner,&refs[1],&radio,&bad));
 bad=ticket;bad.epoch++;
 assert(!wr_iot_mbss_recovery_bind_close(&owner,&refs[1],&radio,&bad));
 assert(wr_iot_mbss_recovery_bind_close(&owner,&refs[1],&radio,&ticket));
 assert(wr_iot_ref_begin_close(&refs[1],&mbss_device,2,1));
 refs[1].close_serial=ticket.serial;refs[1].close_stage=3;
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_CONTINUE_CLOSE);
 assert(!wr_iot_mbss_recovery_mark_completed(&owner,&refs[1],&radio));
 assert(wr_iot_radio_finish(&radio,&ticket,1));
 assert(wr_iot_ref_consume(&refs[1],&mbss_device,2,1));
 refs[1].close_stage=4;
 /* A second radio operation may retire before the deferred worker wakes.
  * The exact IDLE/stage-4 record, not global retired_serial, is its receipt. */
 radio.busy=WR_RADIO_AUX_OPEN;
 radio.retired_serial=ticket.serial+1;
 refs[1].close_stage=3;
 assert(!wr_iot_mbss_recovery_mark_completed(&owner,&refs[1],&radio));
 refs[1].close_stage=4;
 assert(wr_iot_mbss_recovery_mark_completed(&owner,&refs[1],&radio));
 radio.busy=0;
 assert(!wr_iot_mbss_recovery_complete(&owner,0));
 assert(wr_iot_mbss_recovery_complete(&owner,1));

 /* A failed abort before a confirmed virtual-UP has no retryable DOWN. */
 wr_iot_mbss_recovery_init(&owner);
 refs[1].phase=WR_REF_UNCERTAIN_OPEN;refs[1].close_stage=0;
 assert(wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_UNCERTAIN,0,1,1));
 assert(wr_iot_mbss_recovery_begin(&owner));
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_RECONCILE);
 assert(!wr_iot_mbss_recovery_mark_completed(&owner,&refs[1],&radio));
 assert(wr_iot_mbss_recovery_request_stop(&owner));
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_NONE);
 assert(!wr_iot_mbss_recovery_complete(&owner,1));

 /* A checked close that paused after DOWN admission retains its ticket. */
 wr_iot_mbss_recovery_init(&owner);
 refs[1].phase=WR_REF_CLOSING;refs[1].close_stage=3;
 radio.phase=WR_RADIO_READY;
 assert(wr_iot_radio_begin_stop(&radio,2,&ticket));
 record_ticket(&refs[1],&ticket,2);
 refs[1].close_serial=ticket.serial;
 refs[1].close_vendor_count=1;
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,&ticket,1,1));
 refs[1].close_vendor_count=2;
 bad=ticket;bad.epoch++;
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,&bad,1,1));
 bad=ticket;bad.prior_ready=!ticket.prior_ready;
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,&bad,1,1));
 bad=ticket;bad.operation=WR_RADIO_AUX_CLOSE;
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,&bad,1,1));
 bad=ticket;bad.reset_kind=WR_RADIO_RESET_PDMA;
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,&bad,1,1));
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,0,1,1));
 assert(wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_CLOSE_INCOMPLETE,&ticket,1,1));
 assert(owner.close_ticket_valid&&owner.close_ticket.epoch==ticket.epoch);
 assert(wr_iot_mbss_recovery_begin(&owner));
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_CONTINUE_CLOSE);
 assert(wr_iot_mbss_recovery_copy_close_ticket(&owner,&refs[1],&radio,
                                               refs,2,2,&copy));
 assert(copy.serial==ticket.serial&&copy.epoch==ticket.epoch&&
        copy.operation==ticket.operation);
 radio.epoch++;
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_NONE);
 assert(!wr_iot_mbss_recovery_copy_close_ticket(&owner,&refs[1],&radio,
                                                refs,2,2,&copy));
 radio.epoch--;
 radio.phase=WR_RADIO_CLOSING;radio.epoch++;
 assert(wr_iot_mbss_recovery_copy_close_ticket(&owner,&refs[1],&radio,
                                               refs,2,2,&copy));
 assert(copy.epoch==ticket.epoch);
 radio.epoch--;radio.phase=WR_RADIO_READY;
 radio.serial++;
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_NONE);
 /* An uncertain post-mutation close retains identity for reconciliation,
  * but a different epoch must never authorize it. */
 wr_iot_mbss_recovery_init(&owner);
 radio.busy=WR_RADIO_BSS_CLOSE;
 ticket.serial=radio.serial;ticket.epoch=radio.epoch;
 ticket.operation=WR_RADIO_BSS_CLOSE;
 record_ticket(&refs[1],&ticket,2);
 refs[1].close_serial=ticket.serial;refs[1].close_stage=5;
 bad=ticket;bad.epoch++;
 assert(!wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_UNCERTAIN,&bad,1,1));
 assert(wr_iot_mbss_recovery_queue(&owner,&refs[1],&radio,
   WR_MBSS_RECOVERY_UNCERTAIN,&ticket,1,1));
 assert(wr_iot_mbss_recovery_begin(&owner));
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_RECONCILE);
 radio.epoch++;
 assert(wr_iot_mbss_recovery_action(&owner,&refs[1],&radio,refs,2,2)==
        WR_MBSS_RECOVERY_NONE);
 return 0;
}
