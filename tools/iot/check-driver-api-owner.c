#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "driver-api-owner.h"
int main(void){
 for(unsigned fault=0;fault<9;fault++){
  struct wr_iot_driver_owner o={0};struct wr_iot_radio_transition r;
  struct wr_iot_interface_ref slots[2]={{0}},*main_ref,*iot_ref;
  unsigned long sequence=0;int main_dev=0,iot_dev=0,task=0,other=0;
  struct wr_iot_driver_open_request q={0};
  wr_iot_radio_transition_init(&r);r.phase=WR_RADIO_READY;r.main_ready=1;
  main_ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  iot_ref=wr_iot_registry_add_family(slots,2,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  assert(main_ref&&iot_ref);main_ref->published=iot_ref->published=1;main_ref->phase=WR_REF_OWNED;
  q.adapter_epoch=r.epoch;q.device_generation=iot_ref->generation;memcpy(q.password,"password",9);
  assert(!wr_iot_driver_owner_reserve(&o,&r,slots,2,&main_dev,&iot_dev,1,&task,&q,1,0));
  assert(!wr_iot_driver_owner_reserve(&o,&r,slots,2,&main_dev,&iot_dev,1,&task,&q,0,1));
  assert(wr_iot_driver_owner_reserve(&o,&r,slots,2,&main_dev,&iot_dev,1,&task,&q,0,0));
  assert(r.busy==WR_RADIO_BSS_OPEN&&iot_ref->phase==WR_REF_RESERVED);
  assert(!wr_iot_driver_owner_take(&o,&other,&iot_dev,&r,slots,2));
  assert(!wr_iot_driver_owner_leave(&o,&other,&iot_dev,&r,slots,2)&&o.active);
  if(fault==1){assert(wr_iot_driver_owner_leave(&o,&task,&iot_dev,&r,slots,2));assert(iot_ref->phase==WR_REF_IDLE&&!r.busy);continue;}
  switch(fault){
   case 2:r.reset_pending=1;break;
   case 3:r.epoch++;break;
   case 4:iot_ref->generation++;break;
   case 5:r.pm_suspending=1;break;
   case 6:iot_ref->removing=1;break;
   case 7:r.main_ready=0;break;
  }
  const struct wr_iot_driver_open_request *request=wr_iot_driver_owner_take(&o,&task,&iot_dev,&r,slots,2);
  assert((request!=0)==(fault==0||fault==8));
  if(request){
   assert(!strcmp((const char *)request->password,"password"));
   assert(!wr_iot_driver_owner_take(&o,&task,&iot_dev,&r,slots,2));
   if(fault==0){assert(wr_iot_ref_open_finish(iot_ref,&iot_dev,iot_ref->generation,o.claim.serial,0));assert(wr_iot_radio_abort_bss_open_unmutated(&r,&o.ticket));}
  }
  assert(wr_iot_driver_owner_leave(&o,&task,&iot_dev,&r,slots,2)==(fault==0));
  assert(!o.active&&!o.task&&!o.request.password[0]&&o.poisoned==(fault!=0));
 }
 puts("PASS OPEN request owner: single reserved ticket, control-user exclusion, task binding, one-use consume, pre-ndo cancellation, stale/reset/PM/removal poison and credential cleanup. Lock/lifetime and real driver bindings pending.");return 0;
}
