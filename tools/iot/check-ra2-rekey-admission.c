#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ra2-rekey-admission.h"
#include "driver-api-close-admission.h"
int main(void)
{
 for(unsigned fault=0;fault<44;fault++){
  struct wr_iot_driver_owner owner={0};struct wr_iot_radio_transition radio;
  struct wr_iot_interface_ref slots[3]={{0}},*main_ref,*iot_ref;
  unsigned long sequence=0;int main_dev,iot_dev,guest_dev;
  unsigned users=0,poisoned=0,count=2;int blocked=0;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  main_ref=wr_iot_registry_add_family(slots,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  iot_ref=wr_iot_registry_add_family(slots,3,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  assert(main_ref&&iot_ref);main_ref->published=iot_ref->published=1;
  main_ref->phase=iot_ref->phase=WR_REF_OWNED;main_ref->last_token=1;iot_ref->last_token=2;
  owner.receipt.device=&iot_dev;owner.receipt.epoch=radio.epoch;
  owner.receipt.generation=2;owner.receipt.open_token=2;owner.receipt.valid=1;
  owner.receipt.first_beacon_confirmed=1;owner.receipt.request_id[0]=1;
  switch(fault){
   case 1:owner.active=1;break;case 2:owner.poisoned=1;break;
   case 3:owner.receipt.valid=0;break;case 4:owner.receipt.device=&guest_dev;break;
   case 5:owner.receipt.epoch++;break;case 6:iot_ref->generation++;break;
   case 7:iot_ref->last_token++;break;case 8:iot_ref->phase=WR_REF_CLOSING;break;
   case 9:iot_ref->published=0;break;case 10:iot_ref->removing=1;break;
   case 11:iot_ref->close_running=1;break;case 12:iot_ref->close_uncertain_reason=1;break;
   case 13:main_ref->phase=WR_REF_IDLE;break;case 14:main_ref->removing=1;break;
   case 15:radio.reset_pending=1;break;case 16:radio.retiring=1;break;
   case 17:radio.exhausted=1;break;case 18:radio.pm_suspending=1;break;
   case 19:radio.pm_suspended=1;break;case 20:radio.busy=WR_RADIO_BSS_OPEN;break;
   case 21:radio.main_inhibited=1;break;case 22:radio.phase=WR_RADIO_UNVERIFIED;break;
   case 23:users=3;break;case 24:blocked=1;break;case 25:count=1;break;
   case 26:main_ref->last_token=0;break;case 27:main_ref->close_running=1;break;
   case 28:main_ref->close_uncertain_reason=1;break;case 29:main_ref->removal_stage=1;break;
   case 30:iot_ref->removal_stage=1;break;case 31:owner.receipt.first_beacon_confirmed=0;break;
   case 32:poisoned=1;break;case 33:users=~0U;break;
   case 34:{
    struct wr_iot_interface_ref *guest=wr_iot_registry_add_family(slots,3,&sequence,&guest_dev,WR_REF_FAMILY_MBSS);
    assert(guest);guest->published=1;guest->phase=WR_REF_OWNED;guest->last_token=3;count=3;break;
   }
   case 35:radio.main_ready=0;break;
   case 36:radio.epoch=0;owner.receipt.epoch=0;break;
   case 37:iot_ref->family=WR_REF_FAMILY_APCLI;break;
   case 38:main_ref->family=WR_REF_FAMILY_MBSS;break;
   case 39:memset(owner.receipt.request_id,0,16);break;
   case 40:owner.receipt.open_token++;break;
   case 41:owner.receipt.generation=0;break;
   case 42:count=0;break;
  }
  const unsigned before_users=users;
  struct wr_iot_driver_owner before_owner=owner;struct wr_iot_radio_transition before_radio=radio;
  struct wr_iot_interface_ref before_slots[3];memcpy(before_slots,slots,sizeof(slots));
  int accepted=wr_iot_ra2_rekey_admit(&owner,&radio,slots,fault==43?1:3,&main_dev,&iot_dev,count,&users,&poisoned,blocked);
  assert(accepted==(fault==0||fault==23||fault==34));
  assert(users==before_users+(unsigned)accepted);
  assert(poisoned==(fault==32||fault==33));
  assert(!memcmp(&owner,&before_owner,sizeof(owner))&&!memcmp(&radio,&before_radio,sizeof(radio))&&!memcmp(slots,before_slots,sizeof(slots)));
  if(accepted){
   assert(!wr_iot_driver_close_admissible(&owner,owner.receipt.request_id,&radio,slots,3,&main_dev,&iot_dev,radio.epoch,2,2,count,users,0,0));
   --users;assert(users==before_users);
   if(!users)assert(wr_iot_driver_close_admissible(&owner,owner.receipt.request_id,&radio,slots,3,&main_dev,&iot_dev,radio.epoch,2,2,count,users,0,0));
  }
 }
 puts("PASS ra2 rekey counted admission: active receipt/registry identity,44 cases, concurrent control actors allowed, saturation poisoned, CLOSE excluded until callback releases; no RF proof");
 return 0;
}
