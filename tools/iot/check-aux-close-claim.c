#include "aux-close-claim.h"
#include <assert.h>
#include <stdio.h>

int main(void){
 struct wr_iot_radio_transition radio;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_radio_ticket retry;
 struct wr_iot_interface_ref slots[2]={0},*main_ref,*aux_ref;
 unsigned long sequence=0,generation=0;
 int main_dev=0,aux_dev=0;
 wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 main_ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,
                                      WR_REF_FAMILY_MAIN);
 aux_ref=wr_iot_registry_add_family(slots,2,&sequence,&aux_dev,
                                     WR_REF_FAMILY_WDS);
 assert(main_ref&&aux_ref);
 main_ref->published=aux_ref->published=1;
 main_ref->phase=aux_ref->phase=WR_REF_OWNED;
 main_ref->last_token=aux_ref->last_token=1;
 assert(!wr_iot_aux_close_reserve(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_APCLI,2,&ticket,&generation));
 assert(!wr_iot_aux_close_reserve(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,1,&ticket,&generation));
 assert(!wr_iot_aux_close_reserve(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,3,&ticket,&generation));
 assert(!radio.busy&&aux_ref->phase==WR_REF_OWNED);
 assert(wr_iot_aux_close_reserve(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&ticket,&generation));
 assert(ticket.operation==WR_RADIO_AUX_CLOSE&&radio.busy==WR_RADIO_AUX_CLOSE);
 assert(generation==aux_ref->generation&&aux_ref->phase==WR_REF_CLOSING&&
        aux_ref->close_serial==ticket.serial&&aux_ref->close_stage==0);
 assert(!wr_iot_aux_close_reserve(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&ticket,&generation));
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 aux_ref->close_stage=1;
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_APCLI,2,&retry,&generation));
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,1,&retry,&generation));
 assert(wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 assert(retry.serial==ticket.serial&&retry.epoch==ticket.epoch&&
        retry.operation==ticket.operation&&
        retry.prior_phase==ticket.prior_phase&&
        retry.prior_ready==ticket.prior_ready);
 assert(aux_ref->close_stage==3);
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 assert(wr_iot_aux_close_retry_release(&radio,slots,2,&aux_dev,
          generation,&retry));
 assert(aux_ref->close_stage==1);
 radio.virtual_down_stage=2;
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 radio.virtual_down_stage=0;
 wr_iot_radio_request_reset_kind(&radio,WR_RADIO_RESET_PDMA);
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 radio.reset_pending=0;
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation)); /* epoch changed */
 radio.epoch=ticket.epoch;radio.pm_suspending=1;
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 radio.pm_suspending=0;radio.retiring=1;
 assert(!wr_iot_aux_close_retry_unmutated_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 assert(wr_iot_radio_begin(&radio,radio.epoch,WR_RADIO_AUX_CLOSE,&ticket));
 assert(wr_iot_radio_abort_aux_close_unmutated(&radio,&ticket));
 assert(!radio.busy&&radio.retired_serial==ticket.serial);
 slots[0]=(struct wr_iot_interface_ref){0};
 slots[1]=(struct wr_iot_interface_ref){0};sequence=0;
 wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 main_ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,
                                      WR_REF_FAMILY_MAIN);
 aux_ref=wr_iot_registry_add_family(slots,2,&sequence,&aux_dev,
                                     WR_REF_FAMILY_WDS);
 assert(main_ref&&aux_ref);
 main_ref->published=aux_ref->published=1;
 main_ref->phase=aux_ref->phase=WR_REF_OWNED;
 main_ref->last_token=aux_ref->last_token=1;
 assert(wr_iot_aux_close_reserve(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&ticket,&generation));
 aux_ref->close_stage=1;radio.virtual_down_stage=2;
 radio.epoch++; /* late epoch change makes first finish uncertain */
 assert(!wr_iot_aux_close_finalize_after_down(&radio,slots,2,&aux_dev,
          generation,&ticket,1,1));
 assert(aux_ref->close_stage==4&&radio.busy==WR_RADIO_AUX_CLOSE);
 assert(!wr_iot_aux_close_claim_after_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,2,&retry,&generation));
 assert(!wr_iot_aux_close_claim_after_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_APCLI,1,&retry,&generation));
 assert(wr_iot_aux_close_claim_after_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,1,&retry,&generation));
 assert(aux_ref->close_stage==5&&retry.serial==ticket.serial);
 assert(!wr_iot_aux_close_claim_after_down(&radio,slots,2,&aux_dev,
          WR_REF_FAMILY_WDS,1,&retry,&generation));
 radio.reset_pending=WR_RADIO_RESET_PDMA;
 assert(wr_iot_aux_close_finalize_after_down(&radio,slots,2,&aux_dev,
          generation,&retry,5,1));
 assert(aux_ref->phase==WR_REF_IDLE&&aux_ref->close_stage==2&&
        !radio.busy&&radio.reset_pending);
 puts("PASS auxiliary close same-ticket retry and post-DOWN completion gates");
 return 0;
}
