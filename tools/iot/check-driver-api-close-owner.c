#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-owner.h"
int main(void){
 for(unsigned fault=0;fault<12;fault++){
  struct wr_iot_driver_owner open={0};struct wr_iot_driver_close_owner close={0};
  struct wr_iot_radio_transition radio;struct wr_iot_interface_ref slots[2]={{0}};
  int main_dev,iot_dev,task,other;unsigned long sequence=0,generation=0;
  unsigned char nonce[16]={1};struct wr_iot_radio_ticket ticket={0},other_ticket;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  struct wr_iot_interface_ref *main_ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *record=wr_iot_registry_add_family(slots,2,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  main_ref->published=record->published=1;main_ref->phase=record->phase=WR_REF_OWNED;
  main_ref->last_token=1;record->last_token=2;
  open.receipt.device=&iot_dev;open.receipt.epoch=1;open.receipt.generation=2;
  open.receipt.open_token=2;open.receipt.valid=1;memcpy(open.receipt.request_id,nonce,16);
  assert(wr_iot_driver_close_reserve(&close,&open,nonce,&radio,slots,2,&main_dev,&iot_dev,&task,1,2,2,2,0,0,0));
  unsigned long serial=radio.serial;
  assert(radio.busy==WR_RADIO_BSS_CLOSE&&record->close_epoch==1);
  assert(!wr_iot_driver_close_reserve(&close,&open,nonce,&radio,slots,2,&main_dev,&iot_dev,&task,1,2,2,2,0,0,0));
  assert(!wr_iot_radio_begin_stop(&radio,2,&other_ticket)&&radio.serial==serial);
  const void *caller=&task,*device=&iot_dev;
  switch(fault){
   case 1:caller=&other;break;case 2:device=&other;break;
   case 3:record->generation++;break;case 4:record->last_token++;break;
   case 5:record->removing=1;break;case 6:radio.epoch++;break;
   case 7:radio.serial++;break;case 8:record->close_epoch++;break;
   case 9:record->close_running=1;break;
   case 10:record->removal_stage=1;break;
   case 11:close.ticket.reset_kind=1;break;
  }
  assert(wr_iot_driver_close_take(&close,caller,device,&radio,slots,2,&ticket,&generation)==(fault==0));
  assert(close.active&&radio.busy==WR_RADIO_BSS_CLOSE);
  if(!fault){
   assert(generation==2&&ticket.serial==serial&&radio.serial==serial&&close.consumed);
   assert(!wr_iot_driver_close_take(&close,&task,&iot_dev,&radio,slots,2,&ticket,&generation));
  }else assert(!close.consumed&&!generation); /* Exact reservation retained. */
 }
 puts("PASS CLOSE owner: one ticket, one same-task/device consume; identity/race refusals retain reservation, no executor or release bound");
 return 0;
}
