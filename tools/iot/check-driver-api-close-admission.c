#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-admission.h"
int main(void){
 for(unsigned fault=0;fault<29;fault++){
  struct wr_iot_driver_owner owner={0};struct wr_iot_radio_transition radio;
  struct wr_iot_interface_ref slots[3]={{0}},*main_ref,*iot_ref;
  unsigned long sequence=0;int main_dev,iot_dev,guest_dev;
  unsigned char nonce[16]={1};unsigned users=0,count=2;int blocked=0,probe=0;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  main_ref=wr_iot_registry_add_family(slots,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  iot_ref=wr_iot_registry_add_family(slots,3,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  assert(main_ref&&iot_ref);main_ref->published=iot_ref->published=1;
  main_ref->phase=iot_ref->phase=WR_REF_OWNED;main_ref->last_token=1;iot_ref->last_token=2;
  owner.receipt.device=&iot_dev;owner.receipt.epoch=radio.epoch;
  owner.receipt.generation=2;owner.receipt.open_token=2;owner.receipt.valid=1;
  memcpy(owner.receipt.request_id,nonce,16);
  switch(fault){
   case 1:nonce[0]++;break;case 2:owner.active=1;break;case 3:owner.poisoned=1;break;
   case 4:owner.receipt.valid=0;break;case 5:owner.receipt.device=&guest_dev;break;
   case 6:owner.receipt.epoch++;break;case 7:iot_ref->generation++;break;
   case 8:iot_ref->last_token++;break;case 9:iot_ref->phase=WR_REF_CLOSING;break;
   case 10:iot_ref->published=0;break;case 11:iot_ref->removing=1;break;
   case 12:iot_ref->close_running=1;break;case 13:iot_ref->close_uncertain_reason=1;break;
   case 14:main_ref->phase=WR_REF_IDLE;break;case 15:main_ref->removing=1;break;
   case 16:radio.reset_pending=1;break;case 17:radio.retiring=1;break;
   case 18:radio.exhausted=1;break;case 19:radio.pm_suspending=1;break;
   case 20:radio.pm_suspended=1;break;case 21:radio.busy=WR_RADIO_BSS_OPEN;break;
   case 22:radio.main_inhibited=1;break;case 23:radio.phase=WR_RADIO_UNVERIFIED;break;
   case 24:users=1;break;case 25:blocked=1;break;case 26:probe=1;break;case 27:count=1;break;
   case 28:{
    struct wr_iot_interface_ref *guest=wr_iot_registry_add_family(slots,3,&sequence,&guest_dev,WR_REF_FAMILY_MBSS);
    assert(guest);guest->published=1;guest->phase=WR_REF_OWNED;guest->last_token=3;count=3;break;
   }
  }
  struct wr_iot_driver_owner before_owner=owner;struct wr_iot_radio_transition before_radio=radio;
  struct wr_iot_interface_ref before_slots[3];memcpy(before_slots,slots,sizeof(slots));
  assert(wr_iot_driver_close_admissible(&owner,nonce,&radio,slots,3,&main_dev,&iot_dev,1,2,2,count,users,blocked,probe)==(fault==0||fault==28));
  assert(!memcmp(&owner,&before_owner,sizeof(owner))&&!memcmp(&radio,&before_radio,sizeof(radio))&&!memcmp(slots,before_slots,sizeof(slots)));
 }
 puts("PASS close admission: same successful OPEN nonce/epoch/generation/token and owned Main/count with Guest absent/present;27 refusals, no state mutation; ticket transfer/executor unbound");
 return 0;
}
