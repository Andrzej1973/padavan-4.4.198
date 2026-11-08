#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-finish.h"
int main(void){
 for(unsigned fault=0;fault<20;fault++){
  struct wr_iot_driver_close_owner owner={0};struct wr_iot_radio_transition radio;
  struct wr_iot_interface_ref slots[2]={{0}};unsigned long seq=0;
  int main_dev,iot_dev,task,other;const void *caller=&task;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  struct wr_iot_interface_ref *main_ref=wr_iot_registry_add_family(slots,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *record=wr_iot_registry_add_family(slots,2,&seq,&iot_dev,WR_REF_FAMILY_MBSS);
  assert(main_ref&&record);main_ref->published=record->published=1;
  main_ref->phase=WR_REF_OWNED;main_ref->last_token=1;record->last_token=2;
  owner.active=owner.consumed=1;owner.task=&task;owner.device=&iot_dev;
  owner.generation=2;owner.open_token=2;
  owner.ticket.epoch=1;owner.ticket.serial=3;owner.ticket.operation=WR_RADIO_BSS_CLOSE;
  owner.ticket.prior_phase=WR_RADIO_READY;owner.ticket.prior_ready=1;
  record->close_epoch=1;record->close_serial=3;record->close_vendor_count=2;
  record->close_prior_phase=WR_RADIO_READY;record->close_prior_ready=1;record->close_stage=4;
  radio.serial=radio.retired_serial=3;
  switch(fault){
   case 1:owner.active=0;break;case 2:owner.consumed=0;break;case 3:caller=&other;break;
   case 4:owner.ticket.operation=WR_RADIO_CLOSE;break;case 5:radio.epoch++;break;
   case 6:radio.retired_serial++;break;case 7:record->close_serial++;break;
   case 8:record->close_vendor_count=3;break;case 9:record->close_prior_ready=0;break;
   case 10:record->close_stage=3;break;case 11:record->close_running=1;break;
   case 12:record->close_uncertain_reason=WR_CLOSE_UNCERTAIN_DMA;break;
   case 13:record->generation++;break;case 14:record->last_token++;break;
   case 15:radio.reset_pending=1;break;case 16:main_ref->phase=WR_REF_IDLE;break;
   case 17:owner.ticket.reset_kind=1;break;case 18:record->open_unmutated=1;break;
   case 19:radio.busy=WR_RADIO_BSS_OPEN;break;
  }
  struct wr_iot_driver_close_owner before=owner;
  assert(wr_iot_driver_close_reference_completed(&owner,caller,&iot_dev,&radio,slots,2,&main_dev,1)==(fault==0));
  assert(!memcmp(&owner,&before,sizeof(owner)));
  if(fault!=3&&fault!=1){
   assert(wr_iot_driver_close_finish_reference(&owner,caller,&iot_dev,&radio,slots,2,&main_dev,1,0)==(fault==0));
   assert(owner.active&&!owner.task&&owner.reference_completed==(fault==0)&&owner.uncertain==(fault!=0));
   assert(owner.ticket.serial==before.ticket.serial&&owner.device==before.device&&owner.generation==before.generation);
   assert(!wr_iot_driver_close_finish_reference(&owner,caller,&iot_dev,&radio,slots,2,&main_dev,1,0));
  }else{
   assert(!wr_iot_driver_close_finish_reference(&owner,caller,&iot_dev,&radio,slots,2,&main_dev,1,0));
   assert(!memcmp(&owner,&before,sizeof(owner)));
  }
 /* Not even success releases. */
 }
 puts("PASS CLOSE reference completion: exact consumed ticket/retirement/record/count/Main;19 faults refused, finish retains owner/provenance and clears borrowed task, duplicate/wrong owner refuses; no RF/isolation proof");
}
