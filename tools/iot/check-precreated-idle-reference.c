#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "precreated-idle-reference.h"
int main(void){
 for(unsigned fault=0;fault<26;fault++){
  struct wr_iot_radio_transition radio;struct wr_iot_interface_ref slots[3]={0};
  int main_dev,iot_dev,guest_dev;unsigned long sequence=0;unsigned count=1;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(slots,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(slots,3,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  main->published=iot->published=1;main->phase=WR_REF_OWNED;main->last_token=1;
  switch(fault){
   case 1:radio.reset_pending=1;break;case 2:radio.busy=WR_RADIO_BSS_OPEN;break;
   case 3:radio.main_ready=0;break;case 4:radio.pm_suspending=1;break;
   case 5:radio.retiring=1;break;case 6:iot->last_token=2;break;
   case 7:iot->open_unmutated=1;break;case 8:iot->close_serial=2;break;
   case 9:iot->close_stage=4;break;case 10:iot->close_epoch=1;break;
   case 11:iot->phase=WR_REF_OWNED;break;case 12:iot->published=0;break;
   case 13:iot->removing=1;break;case 14:main->removing=1;break;
   case 15:iot->generation++;break;case 16:count=2;break;
   case 17:iot->close_verified_stage=1;break;case 18:iot->close_prior_ready=1;break;
   case 19:radio.epoch=0;break;case 20:radio.exhausted=1;break;
   case 21:main->last_token=0;break;case 22:iot->family=WR_REF_FAMILY_WDS;break;
   case 23:{struct wr_iot_interface_ref *g=wr_iot_registry_add_family(slots,3,&sequence,&guest_dev,WR_REF_FAMILY_MBSS);g->published=1;g->phase=WR_REF_OWNED;g->last_token=3;count=2;break;}
   case 24:radio.epoch++;iot->last_token=2;break;
   case 25:radio.epoch++;iot->close_serial=2;break;
  }
  struct wr_iot_radio_transition before=radio;struct wr_iot_interface_ref saved[3];memcpy(saved,slots,sizeof(saved));
  assert(wr_iot_precreated_idle_reference(&radio,slots,3,&main_dev,&iot_dev,2,count)==(fault==0||fault==23));
  assert(!memcmp(&radio,&before,sizeof(radio))&&!memcmp(slots,saved,sizeof(slots)));
 }
 puts("PASS initial never-opened ra2 software reference: prior OPEN/CLOSE history refused, current Main/Guest count and reset/PM/removal checked; no hardware or RF proof");
 return 0;
}
