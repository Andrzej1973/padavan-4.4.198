#include "virtual-open-claim.h"
#include <assert.h>
#include <stdio.h>

int main(void){
 struct wr_iot_radio_transition radio;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref records[1]={{0}},*record;
 struct wr_iot_virtual_open_claim claim;
 unsigned long sequence=0,old_generation;
 int device=0,other=0;
 wr_iot_radio_transition_init(&radio);
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 record=wr_iot_registry_add(records,1,&sequence,&device);
 assert(record);record->published=1;
 assert(wr_iot_radio_begin(&radio,radio.epoch,WR_RADIO_BSS_OPEN,&ticket));
 assert(wr_iot_ref_reserve(record,&device,record->generation,ticket.serial));
 claim=(struct wr_iot_virtual_open_claim){&device,record->generation,
   ticket.serial,ticket.epoch,WR_RADIO_BSS_OPEN};
 assert(wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 radio.virtual_up_stage=1;
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 radio.virtual_up_stage=0;
 claim.device=&other;
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 claim.device=&device;claim.generation++;
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 claim.generation=record->generation;claim.serial++;
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 claim.serial=ticket.serial;claim.operation=WR_RADIO_AUX_OPEN;
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 claim.operation=WR_RADIO_BSS_OPEN;
 wr_iot_radio_request_reset(&radio);
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 assert(wr_iot_radio_finish(&radio,&ticket,0));
 assert(wr_iot_ref_open_finish(record,&device,record->generation,
                              ticket.serial,0));
 old_generation=record->generation;
 assert(wr_iot_registry_begin_remove(record,&device,old_generation));
 assert(wr_iot_registry_kernel_done(record,&device,old_generation));
 assert(wr_iot_registry_vendor_done(record,&device,old_generation));
 assert(wr_iot_registry_release(record,&device,old_generation));
 record=wr_iot_registry_add(records,1,&sequence,&device);
 assert(record&&record->generation!=old_generation);
 record->published=1;
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));

 wr_iot_radio_transition_init(&radio);
 assert(wr_iot_radio_begin_aux_open(&radio,0,&ticket));
 assert(wr_iot_ref_reserve(record,&device,record->generation,ticket.serial));
 claim=(struct wr_iot_virtual_open_claim){&device,record->generation,
   ticket.serial,ticket.epoch,WR_RADIO_AUX_START};
 assert(wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 wr_iot_radio_main_down(&radio);
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 assert(wr_iot_ref_open_finish(record,&device,record->generation,
                              ticket.serial,0));
 wr_iot_radio_transition_init(&radio);
 radio.serial=2;radio.phase=WR_RADIO_READY;
 radio.main_inhibited=1;radio.main_ready=0;
 assert(wr_iot_radio_begin_aux_open(&radio,1,&ticket));
 assert(ticket.operation==WR_RADIO_AUX_OPEN);
 assert(wr_iot_ref_reserve(record,&device,record->generation,ticket.serial));
 claim=(struct wr_iot_virtual_open_claim){&device,record->generation,
   ticket.serial,ticket.epoch,WR_RADIO_AUX_OPEN};
 assert(wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 wr_iot_radio_request_reset(&radio);
 assert(!wr_iot_virtual_open_claim_matches(&claim,&radio,records,1));
 /* The main interface must match adapter identity and the first-open count. */
 {struct wr_iot_radio_transition main_radio;
  struct wr_iot_radio_ticket main_ticket;
  struct wr_iot_interface_ref main_refs[1]={{0}},*main_ref;
  struct wr_iot_virtual_open_claim main_claim;
  unsigned long main_seq=0;
  wr_iot_radio_transition_init(&main_radio);
  main_ref=wr_iot_registry_add(main_refs,1,&main_seq,&other);
  assert(main_ref);main_ref->published=1;
  assert(wr_iot_radio_begin(&main_radio,main_radio.epoch,WR_RADIO_START,&main_ticket));
  assert(wr_iot_ref_reserve(main_ref,&other,main_ref->generation,main_ticket.serial));
  main_claim=(struct wr_iot_virtual_open_claim){&other,main_ref->generation,
    main_ticket.serial,main_ticket.epoch,WR_RADIO_START};
  assert(wr_iot_virtual_main_open_claim_matches(&main_claim,&main_radio,
    main_refs,1,&other,0));
  assert(!wr_iot_virtual_main_open_claim_matches(&main_claim,&main_radio,
    main_refs,1,&device,0));
  assert(!wr_iot_virtual_main_open_claim_matches(&main_claim,&main_radio,
    main_refs,1,&other,1));
  main_radio.virtual_up_stage=1;
  assert(!wr_iot_virtual_main_open_claim_matches(&main_claim,&main_radio,
    main_refs,1,&other,0));
  main_radio.virtual_up_stage=0;
  assert(wr_iot_ref_open_finish(main_ref,&other,main_ref->generation,
    main_ticket.serial,0));
  assert(wr_iot_radio_finish(&main_radio,&main_ticket,0));
  wr_iot_radio_transition_init(&main_radio);
  main_radio.phase=WR_RADIO_UNVERIFIED;
  main_radio.main_inhibited=1;
  main_radio.serial=main_ticket.serial;
  assert(wr_iot_radio_begin(&main_radio,main_radio.epoch,
    WR_RADIO_MAIN_OPEN,&main_ticket));
  assert(wr_iot_ref_reserve(main_ref,&other,main_ref->generation,
    main_ticket.serial));
  main_claim=(struct wr_iot_virtual_open_claim){&other,main_ref->generation,
    main_ticket.serial,main_ticket.epoch,WR_RADIO_MAIN_OPEN};
  assert(wr_iot_virtual_main_open_claim_matches(&main_claim,&main_radio,
    main_refs,1,&other,1));
  assert(!wr_iot_virtual_main_open_claim_matches(&main_claim,&main_radio,
    main_refs,1,&other,0));
  wr_iot_radio_request_reset(&main_radio);
  assert(!wr_iot_virtual_main_open_claim_matches(&main_claim,&main_radio,
    main_refs,1,&other,1));
 }
 /* Main admission reserves ticket and record together before vendor calls. */
 {struct wr_iot_radio_transition main_radio;
  struct wr_iot_radio_ticket main_ticket;
  struct wr_iot_interface_ref main_refs[1]={{0}},*main_ref;
  unsigned long main_seq=0,generation=0;
  wr_iot_radio_transition_init(&main_radio);
  main_ref=wr_iot_registry_add(main_refs,1,&main_seq,&other);
  assert(main_ref);main_ref->published=1;
  assert(wr_iot_main_open_reserve(&main_radio,main_refs,1,&other,0,
    &main_ticket,&generation));
  assert(main_ticket.operation==WR_RADIO_START&&
    main_ref->phase==WR_REF_RESERVED&&generation==main_ref->generation);
  assert(!wr_iot_main_open_reserve(&main_radio,main_refs,1,&other,0,
    &main_ticket,&generation));
  assert(wr_iot_ref_open_finish(main_ref,&other,generation,
    main_ticket.serial,0));
  assert(wr_iot_radio_finish(&main_radio,&main_ticket,0));
  main_radio.phase=WR_RADIO_UNVERIFIED;
  assert(wr_iot_main_open_reserve(&main_radio,main_refs,1,&other,1,
    &main_ticket,&generation));
  assert(main_ticket.operation==WR_RADIO_MAIN_OPEN);
  assert(wr_iot_ref_open_finish(main_ref,&other,generation,
    main_ticket.serial,1));
  assert(wr_iot_radio_finish_unverified(&main_radio,&main_ticket));
  assert(!wr_iot_main_open_reserve(&main_radio,main_refs,1,&other,1,
    &main_ticket,&generation));
  wr_iot_ref_init(main_ref,&other,2);main_ref->published=1;
  main_ref->last_token=99;
  wr_iot_radio_transition_init(&main_radio);
  assert(!wr_iot_main_open_reserve(&main_radio,main_refs,1,&other,0,
    &main_ticket,&generation));
  assert(!main_radio.busy&&main_radio.phase==WR_RADIO_DOWN&&
    main_ref->phase==WR_REF_IDLE);
  assert(!wr_iot_main_open_reserve(&main_radio,main_refs,1,&other,~0U,
    &main_ticket,&generation));
 }
 /* Auxiliary admission must reserve its exact owner before any mutation. */
 {struct wr_iot_radio_transition aux_radio;
  struct wr_iot_radio_ticket aux_ticket;
  struct wr_iot_interface_ref aux_refs[1]={{0}},*aux_ref;
  struct wr_iot_virtual_open_claim aux_claim;
  unsigned long aux_seq=0,generation=0;
  wr_iot_radio_transition_init(&aux_radio);
  aux_ref=wr_iot_registry_add_family(aux_refs,1,&aux_seq,&device,
    WR_REF_FAMILY_APCLI);
  assert(aux_ref);aux_ref->published=1;
  assert(!wr_iot_aux_open_reserve(&aux_radio,aux_refs,1,&other,
    WR_REF_FAMILY_APCLI,0,
    &aux_ticket,&generation));
  assert(!wr_iot_aux_open_reserve(&aux_radio,aux_refs,1,&device,
    WR_REF_FAMILY_APCLI,~0U,
    &aux_ticket,&generation));
  assert(!wr_iot_aux_open_reserve(&aux_radio,aux_refs,1,&device,
    WR_REF_FAMILY_MBSS,0,&aux_ticket,&generation));
  assert(!wr_iot_aux_open_reserve(&aux_radio,aux_refs,1,&device,
    WR_REF_FAMILY_WDS,0,&aux_ticket,&generation));
  assert(wr_iot_aux_open_reserve(&aux_radio,aux_refs,1,&device,
    WR_REF_FAMILY_APCLI,0,
    &aux_ticket,&generation));
  assert(aux_ticket.operation==WR_RADIO_AUX_START&&
    aux_ref->phase==WR_REF_RESERVED&&generation==aux_ref->generation);
  aux_claim=(struct wr_iot_virtual_open_claim){&device,generation,
    aux_ticket.serial,aux_ticket.epoch,WR_RADIO_AUX_START};
  assert(wr_iot_virtual_open_claim_matches(&aux_claim,&aux_radio,aux_refs,1));
  assert(wr_iot_virtual_aux_open_claim_matches(&aux_claim,&aux_radio,
    aux_refs,1,&other,0));
  assert(!wr_iot_virtual_aux_open_claim_matches(&aux_claim,&aux_radio,
    aux_refs,1,&device,0));
  assert(!wr_iot_virtual_aux_open_claim_matches(&aux_claim,&aux_radio,
    aux_refs,1,&other,1));
  aux_ref->family=WR_REF_FAMILY_MBSS;
  assert(!wr_iot_virtual_aux_open_claim_matches(&aux_claim,&aux_radio,
    aux_refs,1,&other,0));
  aux_ref->family=WR_REF_FAMILY_APCLI;
  assert(!wr_iot_aux_open_reserve(&aux_radio,aux_refs,1,&device,
    WR_REF_FAMILY_APCLI,0,
    &aux_ticket,&generation));
  assert(wr_iot_ref_open_finish(aux_ref,&device,generation,
    aux_ticket.serial,0));
  assert(wr_iot_radio_finish(&aux_radio,&aux_ticket,0));
  aux_radio.phase=WR_RADIO_READY;
  assert(wr_iot_aux_open_reserve(&aux_radio,aux_refs,1,&device,
    WR_REF_FAMILY_APCLI,1,
    &aux_ticket,&generation));
  assert(aux_ticket.operation==WR_RADIO_AUX_OPEN);
  assert(!wr_iot_virtual_open_claim_matches(&aux_claim,&aux_radio,aux_refs,1));
  aux_claim=(struct wr_iot_virtual_open_claim){&device,generation,
    aux_ticket.serial,aux_ticket.epoch,WR_RADIO_AUX_OPEN};
  assert(wr_iot_virtual_open_claim_matches(&aux_claim,&aux_radio,aux_refs,1));
  assert(wr_iot_virtual_aux_open_claim_matches(&aux_claim,&aux_radio,
    aux_refs,1,&other,1));
  assert(!wr_iot_virtual_aux_open_claim_matches(&aux_claim,&aux_radio,
    aux_refs,1,&other,0));
  wr_iot_radio_request_reset(&aux_radio);
  assert(!wr_iot_virtual_open_claim_matches(&aux_claim,&aux_radio,aux_refs,1));
  assert(!wr_iot_virtual_aux_open_claim_matches(&aux_claim,&aux_radio,
    aux_refs,1,&other,1));
 }
 /* A successful hardware observation is insufficient without the current
  * main reference, matching vendor count and unrevoked VERIFY ticket. */
 for(int mode=0;mode<7;mode++){
  struct wr_iot_radio_transition verified_radio;
  struct wr_iot_radio_ticket open_ticket,verify_ticket,bss_ticket;
  struct wr_iot_interface_ref refs[1]={{0}},*main_ref;
  unsigned long seq=0;
  unsigned int vendor_count=mode==1?2U:1U;
  wr_iot_radio_transition_init(&verified_radio);
  main_ref=wr_iot_registry_add_family(refs,1,&seq,&device,
    WR_REF_FAMILY_MAIN);
  assert(main_ref);main_ref->published=1;
  assert(wr_iot_radio_begin(&verified_radio,verified_radio.epoch,
    WR_RADIO_START,&open_ticket));
  assert(wr_iot_ref_reserve(main_ref,&device,seq,open_ticket.serial));
  assert(wr_iot_ref_open_finish(main_ref,&device,seq,open_ticket.serial,1));
  assert(wr_iot_radio_finish_unverified(&verified_radio,&open_ticket));
  assert(wr_iot_radio_begin(&verified_radio,verified_radio.epoch,
    WR_RADIO_VERIFY,&verify_ticket));
  if(mode==2)main_ref->family=WR_REF_FAMILY_MBSS;
  if(mode==3)main_ref->published=0;
  if(mode==4)main_ref->removing=1;
  if(mode==6)wr_iot_radio_main_down(&verified_radio);
  assert(wr_iot_main_radio_verify_owned(&verified_radio,refs,1,&device,
    vendor_count,&verify_ticket,mode!=5)==(mode==0));
  assert(!verified_radio.busy);
  assert(verified_radio.main_ready==(mode==0));
  assert(wr_iot_radio_begin(&verified_radio,verified_radio.epoch,
    WR_RADIO_BSS_OPEN,&bss_ticket)==(mode==0));
 }
 /* A guest receipt can leave READY for the following IoT open only when its
  * own published reference, total count, ticket and readback all agree. */
 for(int mode=0;mode<5;mode++){
  struct wr_iot_radio_transition bss_radio;
  struct wr_iot_radio_ticket bss_open,next;
  struct wr_iot_interface_ref refs[2]={{0}},*main_ref,*guest_ref;
  unsigned long seq=0;
  wr_iot_radio_transition_init(&bss_radio);
  bss_radio.phase=WR_RADIO_READY;bss_radio.main_ready=1;
  main_ref=wr_iot_registry_add_family(refs,2,&seq,&device,
    WR_REF_FAMILY_MAIN);
  guest_ref=wr_iot_registry_add_family(refs,2,&seq,&other,
    WR_REF_FAMILY_MBSS);
  assert(main_ref&&guest_ref);
  main_ref->published=guest_ref->published=1;
  main_ref->phase=WR_REF_OWNED;
  assert(wr_iot_radio_begin(&bss_radio,bss_radio.epoch,
    WR_RADIO_BSS_OPEN,&bss_open));
  assert(wr_iot_ref_reserve(guest_ref,&other,guest_ref->generation,
    bss_open.serial));
  assert(wr_iot_ref_open_finish(guest_ref,&other,guest_ref->generation,
    bss_open.serial,1));
  if(mode==2)guest_ref->family=WR_REF_FAMILY_APCLI;
  if(mode==4)wr_iot_radio_request_reset(&bss_radio);
  assert(wr_iot_bss_open_finish_observed(&bss_radio,refs,2,&other,
    mode==1?1U:2U,&bss_open,mode!=3)==(mode==0));
  assert(!bss_radio.busy);
  assert(wr_iot_radio_begin(&bss_radio,bss_radio.epoch,
    WR_RADIO_BSS_OPEN,&next)==(mode==0));
 }
 puts("PASS virtual open claim: main and MBSS readback require owned references, count and live tickets");
 return 0;
}
