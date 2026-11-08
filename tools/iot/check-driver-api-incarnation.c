/* Regression: stale numeric query identities can repeat after
 * adapter reconstruction. No hardware/open mutation is executed here. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-owner.h"
int main(void){
 struct wr_iot_driver_open_request stale={0};unsigned int accepted=0;
 int main_dev=0,iot_dev=0,task=0;
 for(unsigned incarnation=0;incarnation<2;incarnation++){
  struct wr_iot_radio_transition radio;struct wr_iot_driver_owner owner={0};
  struct wr_iot_interface_ref slots[2]={{0}},*ref;unsigned long sequence=0;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);assert(ref);ref->published=1;ref->phase=WR_REF_OWNED;
  ref=wr_iot_registry_add_family(slots,2,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);assert(ref);ref->published=1;
  if(!incarnation){stale.adapter_epoch=radio.epoch;stale.device_generation=ref->generation;stale.request_id[0]=1;stale.ssid_length=3;stale.password_length=8;memcpy(stale.ssid,"IoT",3);memcpy(stale.password,"password",8);
   unsigned char wire[144];assert(wr_iot_driver_open_encode(wire,sizeof(wire),&stale));}
  if(!incarnation)assert(wr_iot_driver_owner_query(&owner,stale.request_id,stale.adapter_epoch,stale.device_generation));
  accepted+=wr_iot_driver_owner_reserve(&owner,&radio,slots,2,&main_dev,&iot_dev,1,&task,&stale,0,0)!=0;
 }
 assert(accepted==1);
 puts("PASS stale OPEN refused after owner reconstruction despite repeated epoch/generation; fresh owner has no query challenge. No hardware/open mutation modeled.");return 0;
}
