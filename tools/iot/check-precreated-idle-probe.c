#include <assert.h>
#include <stdio.h>
#include "precreated-idle-probe.h"
int main(void){
 for(unsigned fault=0;fault<10;fault++){
  struct wr_iot_radio_transition r;struct wr_iot_interface_ref slots[2]={0};
  struct wr_iot_precreated_idle_probe p={0};int main_dev,iot_dev;unsigned long seq=0;
  wr_iot_radio_transition_init(&r);r.phase=WR_RADIO_READY;r.main_ready=1;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(slots,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(slots,2,&seq,&iot_dev,WR_REF_FAMILY_MBSS);
  main->published=iot->published=1;main->phase=WR_REF_OWNED;main->last_token=1;
  assert(wr_iot_precreated_idle_probe_begin(&p,&r,slots,2,&main_dev,&iot_dev,2,1));
  assert(!wr_iot_precreated_idle_probe_begin(&p,&r,slots,2,&main_dev,&iot_dev,2,1));
  int observed=1;
  switch(fault){
   case 1:observed=0;break;case 2:assert(wr_iot_radio_request_reset_kind(&r,WR_RADIO_RESET_PDMA));break;
   case 3:r.pm_suspending=1;break;case 4:iot->last_token=3;break;
   case 5:iot->generation++;break;case 6:main->removing=1;break;
   case 7:r.serial++;break;case 8:r.busy=WR_RADIO_BSS_OPEN;break;
   case 9:observed=-1;break;
  }
  assert(wr_iot_precreated_idle_probe_finish(&p,&r,slots,2,1,observed)==(fault==0));
  if(fault==7||fault==8){assert(p.active);continue;}
  assert(!p.active&&!r.busy&&r.retired_serial==p.ticket.serial);
  assert(wr_iot_precreated_idle_probe_current(&p,&r,slots,2,&main_dev,&iot_dev,2,1)==(fault==0));
  if(!fault){
   p.accepted=0;assert(!wr_iot_precreated_idle_probe_current(&p,&r,slots,2,&main_dev,&iot_dev,2,1));p.accepted=1;
   r.serial++;assert(!wr_iot_precreated_idle_probe_current(&p,&r,slots,2,&main_dev,&iot_dev,2,1));r.serial--;
   assert(!wr_iot_precreated_idle_probe_current(&p,&r,slots,2,&main_dev,&iot_dev,3,1));
  }
  assert(!wr_iot_precreated_idle_probe_finish(&p,&r,slots,2,1,1));
  if(fault==2)assert(r.reset_pending&&!r.main_ready);
  if(fault==3)assert(r.pm_suspending);
 }
 puts("PASS persistent initial-idle probe: exact observation ticket, reset/PM/registry drift refusal, failed readback retirement and foreign-ticket context retention; hardware unbound");
 return 0;
}
