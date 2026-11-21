#include <assert.h>
#include <stdio.h>
#include "mbss-closed-probe.h"
int main(void){
 for(unsigned fault=0;fault<9;fault++){
  struct wr_iot_radio_transition r;struct wr_iot_mbss_closed_probe p={0};
  struct wr_iot_interface_ref slots[2]={{0}},*main_ref,*iot_ref;
  int main_dev=0,iot_dev=0,observed=1;unsigned long sequence=0;
  wr_iot_radio_transition_init(&r);r.phase=WR_RADIO_READY;r.main_ready=1;
  main_ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  iot_ref=wr_iot_registry_add_family(slots,2,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  main_ref->published=iot_ref->published=1;main_ref->phase=WR_REF_OWNED;main_ref->last_token=1;
  iot_ref->last_token=2;iot_ref->close_serial=3;iot_ref->close_epoch=r.epoch;iot_ref->close_vendor_count=2;iot_ref->close_stage=4;
  assert(wr_iot_mbss_closed_probe_begin(&p,&r,slots,2,&main_dev,&iot_dev,2,2,3,1));
  assert(r.main_ready&&r.phase==WR_RADIO_READY&&r.busy==WR_RADIO_BSS_OBSERVE);
  assert(!wr_iot_radio_finish(&r,&p.ticket,0)&&r.main_ready);
  assert(!wr_iot_mbss_closed_probe_begin(&p,&r,slots,2,&main_dev,&iot_dev,2,2,3,1));
  switch(fault){
   case 1:observed=0;break;case 2:observed=2;break;
   case 3:wr_iot_radio_request_reset(&r);break;
   case 4:wr_iot_radio_main_down(&r);break;
   case 5:iot_ref->generation++;break;case 6:iot_ref->close_serial++;break;
   case 7:r.pm_suspending=1;break;case 8:main_ref->removing=1;break;
  }
  int prior_ready=r.main_ready;enum wr_iot_radio_phase prior_phase=r.phase;
  int prior_reset=r.reset_pending,prior_pm=r.pm_suspending;
  assert(wr_iot_mbss_closed_probe_finish(&p,&r,slots,2,1,observed)==(fault==0));
  assert(!p.active&&!r.busy&&r.retired_serial==p.ticket.serial);
  assert(r.main_ready==prior_ready&&r.phase==prior_phase&&r.reset_pending==prior_reset&&r.pm_suspending==prior_pm);
  assert(!wr_iot_mbss_closed_probe_finish(&p,&r,slots,2,1,1));
 }
 puts("PASS closed observation ticket: no Main readiness changes on IoT readback failure, stale/reset/PM/removal refusal, exact retirement and replay refusal. Configuration model only; no RF acceptance.");return 0;
}
