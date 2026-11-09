/* Reuse actual adapter binding and its fixture types, not a second mock lock. */
#define main wr_iot_existing_owner_binding_test
#include "check-driver-api-owner-binding.c"
#undef main
int main(void)
{
 for(unsigned fault=0;fault<25;fault++){
  RTMP_ADAPTER ad={.mt7603=1,.vendor_count=1,.ApCfg.BssidNum=3};
  device main_dev={1},dev={1};unsigned long sequence=0;
  struct wr_iot_driver_open_request request={0};
  struct wr_iot_virtual_open_claim snapshot={0},prior={0};
  struct wr_iot_interface_ref *m,*ref;
  ad.net_dev=&main_dev;ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
  locked=1;wr_iot_radio_transition_init(&ad.wr_iot_transition);
  ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  m=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  ref=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&dev,WR_REF_FAMILY_MBSS);
  assert(m&&ref);m->published=ref->published=1;m->phase=WR_REF_OWNED;
  request.request_id[0]=1;request.adapter_epoch=ad.wr_iot_transition.epoch;
  request.device_generation=ref->generation;
  assert(wr_iot_driver_owner_query(&ad.wr_iot_driver_owner,request.request_id,request.adapter_epoch,request.device_generation));
  assert(wr_iot_driver_request_enter(&ad,&dev,&request,current)==0);
  assert(!wr_iot_driver_first_beacon_owner_snapshot(&ad,&dev,&snapshot));
  assert(wr_iot_driver_owner_take(&ad.wr_iot_driver_owner,current,&dev,&ad.wr_iot_transition,ad.wr_iot_interface_refs,3));
  ad.wr_iot_driver_owner.mutation_started=1;
  assert(wr_iot_ref_open_finish(ref,&dev,ref->generation,ad.wr_iot_driver_owner.claim.serial,1));
  ad.vendor_count=2;
  assert(wr_iot_bss_open_finish_observed(&ad.wr_iot_transition,ad.wr_iot_interface_refs,3,&dev,2,&ad.wr_iot_driver_owner.ticket,1));
  assert(wr_iot_driver_first_beacon_owner_snapshot(&ad,&dev,&snapshot));prior=snapshot;
  switch(fault){
   case 1:ad.wr_iot_transition.reset_pending=1;break;
   case 2:ad.wr_iot_transition.epoch++;break;
   case 3:ref->generation++;break;
   case 4:ref->last_token++;break;
   case 5:m->removing=1;break;
   case 6:m->phase=WR_REF_IDLE;break;
   case 7:ad.vendor_count=1;break;
   case 8:ad.wr_iot_driver_owner.task=&ad;break;
   case 9:ad.wr_iot_driver_owner.ticket.serial++;break;
   case 10:ad.wr_iot_driver_owner.consumed=0;break;
   case 11:ad.wr_iot_driver_owner.mutation_started=0;break;
   case 12:ad.wr_iot_transition.pm_suspending=1;break;
   case 13:ad.wr_iot_transition.pm_suspended=1;break;
   case 14:ad.wr_iot_transition.busy=WR_RADIO_RESET;break;
   case 15:ad.wr_iot_driver_owner.active=0;break;
   case 16:ad.wr_iot_driver_owner.poisoned=1;break;
   case 17:ref->published=0;break;
   case 18:ad.wr_iot_transition.main_ready=0;break;
   case 19:ad.wr_iot_close_owner.active=1;break;
   case 20:ad.wr_iot_control_poisoned=1;break;
   case 21:main_dev.running=0;break;
   case 22:dev.running=0;break;
   case 23:locked=0;break;
   case 24:ad.wr_iot_driver_owner.request.device_generation++;break;
  }
  struct wr_iot_driver_owner owner_before=ad.wr_iot_driver_owner;
  assert(wr_iot_driver_first_beacon_owner_snapshot(&ad,&dev,&snapshot)==(fault==0));
  assert(!ad.wr_iot_transition_lock&&!memcmp(&snapshot,&prior,sizeof(snapshot)));
  assert(!memcmp(&owner_before,&ad.wr_iot_driver_owner,sizeof(owner_before)));
  if(!fault){
   struct wr_iot_virtual_open_claim wrong=prior;wrong.serial++;
   assert(!wr_iot_driver_first_beacon_confirm(&ad,&dev,&wrong));
   assert(!ad.wr_iot_driver_owner.receipt.first_beacon_confirmed);
   assert(wr_iot_driver_first_beacon_confirm(&ad,&dev,&prior));
   assert(ad.wr_iot_driver_owner.receipt.first_beacon_confirmed==1);
   assert(!wr_iot_driver_first_beacon_confirm(&ad,&dev,&prior));
  }else{
   assert(!wr_iot_driver_first_beacon_confirm(&ad,&dev,&prior));
   assert(!ad.wr_iot_driver_owner.receipt.first_beacon_confirmed);
  }
 }
 puts("PASS actual post-open owner snapshot: retired ticket/owned reference, task/epoch/generation/count and Main lifetime required;24 faults refuse without mutation. No wait/RF acceptance.");
 return 0;
}
