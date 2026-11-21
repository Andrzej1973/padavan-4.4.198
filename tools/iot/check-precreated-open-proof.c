#include "precreated-open-proof.h"
#include <assert.h>
#include <stdio.h>
int main(void){
 for(unsigned fault=0;fault<15;fault++){
  struct wr_iot_radio_transition r;struct wr_iot_radio_ticket t;
  struct wr_iot_interface_ref slots[1]={{0}},*record;unsigned long seq=0;
  struct wr_iot_precreated_open_proof proof={0};int dev=0,other=0;
  wr_iot_radio_transition_init(&r);r.phase=WR_RADIO_READY;r.main_ready=1;
  record=wr_iot_registry_add(slots,1,&seq,&dev);assert(record);record->published=1;record->family=WR_REF_FAMILY_MBSS;
  assert(wr_iot_radio_begin(&r,r.epoch,WR_RADIO_BSS_OPEN,&t));
  assert(wr_iot_ref_reserve(record,&dev,record->generation,t.serial));
  struct wr_iot_virtual_open_claim c={&dev,record->generation,t.serial,t.epoch,WR_RADIO_BSS_OPEN};
  assert(!wr_iot_precreated_open_observe_begin(&proof,&c,&r,slots,1,&dev,0));
  assert(wr_iot_precreated_open_observe_begin(&proof,&c,&r,slots,1,&dev,10));
  assert(!wr_iot_precreated_open_observe_begin(&proof,&c,&r,slots,1,&dev,10));
  unsigned long long request=10;int observed=1;
  switch(fault){
   case 1:wr_iot_radio_request_reset(&r);break;
   case 2:wr_iot_radio_request_close(&r);break;
   case 3:wr_iot_radio_main_down(&r);break;
   case 4:r.pm_suspending=1;break;
   case 5:r.retiring=1;break;
   case 6:record->generation++;break;
   case 7:record->removing=1;break;
   case 8:record->family=WR_REF_FAMILY_MAIN;break;
   case 9:c.device=&other;break;
   case 10:c.serial++;break;
   case 11:request++;break;
   case 12:observed=0;break;
   case 13:observed=2;break;
   case 14:r.virtual_up_stage=1;break;
  }
  assert(wr_iot_precreated_open_observe_finish(&proof,&c,&r,slots,1,&dev,request,observed)==(fault==0));
  assert(!proof.pending&&!proof.request_generation);
  assert(!wr_iot_precreated_open_observe_finish(&proof,&c,&r,slots,1,&dev,10,1));
 }
 puts("PASS precreated proof binds existing ticket, netdev generation and request generation; reset/close/PM/removal/mismatch/replay refuse. Caller config lease and actual readback are not injected guarantees.");return 0;
}
