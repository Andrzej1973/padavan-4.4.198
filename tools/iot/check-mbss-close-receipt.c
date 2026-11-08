#include <assert.h>
#include <stdio.h>
#include "mbss-close-receipt.h"
int main(void){
 for(unsigned fault=0;fault<18;fault++){
  struct wr_iot_radio_transition r;struct wr_iot_interface_ref slots[2]={{0}},*main_ref,*iot_ref;
  int main_dev=0,iot_dev=0;unsigned long sequence=0;unsigned count=1;
  wr_iot_radio_transition_init(&r);r.phase=WR_RADIO_READY;r.main_ready=1;
  main_ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  iot_ref=wr_iot_registry_add_family(slots,2,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  assert(main_ref&&iot_ref);main_ref->published=iot_ref->published=1;main_ref->phase=WR_REF_OWNED;main_ref->last_token=1;
  iot_ref->last_token=2;iot_ref->close_serial=3;iot_ref->close_epoch=r.epoch;
  iot_ref->close_vendor_count=2;iot_ref->close_stage=4;
  r.serial=10;r.retired_serial=9; /* Later unrelated completion is valid. */
  switch(fault){
   case 1:iot_ref->phase=WR_REF_CLOSING;break;
   case 2:iot_ref->close_stage=3;break;
   case 3:iot_ref->close_running=1;break;
   case 4:iot_ref->close_uncertain_reason=WR_CLOSE_UNCERTAIN_DMA;break;
   case 5:iot_ref->generation++;break;
   case 6:iot_ref->last_token++;break;
   case 7:iot_ref->close_serial++;break;
   case 8:iot_ref->close_epoch++;break;
   case 9:iot_ref->close_vendor_count=1;break;
   case 10:iot_ref->open_unmutated=1;break;
   case 11:main_ref->phase=WR_REF_IDLE;break;
   case 12:main_ref->removing=1;break;
   case 13:r.reset_pending=1;break;
   case 14:r.pm_suspending=1;break;
   case 15:r.phase=WR_RADIO_UNVERIFIED;break;
   case 16:count=2;break;
   case 17:iot_ref->published=0;break;
  }
  assert(wr_iot_mbss_closed_reference(&r,slots,2,&main_dev,&iot_dev,2,2,3,count)==(fault==0));
 }
 puts("PASS exact nonlast-BSS close reference receipt: local stage/token/epoch, owned Main/count; 17 invalid states refuse. Global retired serial not substituted; no RF/DMA/TxS proof.");return 0;
}
