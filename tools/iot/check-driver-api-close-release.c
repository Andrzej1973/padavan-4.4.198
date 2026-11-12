#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-release.h"
int main(void)
{
 for(unsigned int fault=0;fault<15;fault++){
  int main_dev,device;
  unsigned long sequence=0;
  struct wr_iot_interface_ref slots[2]={0};
  struct wr_iot_radio_transition radio;
  struct wr_iot_driver_close_owner close={0};
  struct wr_iot_driver_owner open={0};
  struct wr_iot_driver_close_request request={{1},1,2,3};
  struct wr_iot_mbss_closed_probe probe={0};
  struct wr_iot_beacon_producer_gate producer={7,0,0};
  wr_iot_radio_transition_init(&radio);
  radio.phase=WR_RADIO_READY;radio.main_ready=1;radio.retired_serial=5;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(slots,2,&sequence,&device,WR_REF_FAMILY_MBSS);
  main->published=1;main->phase=WR_REF_OWNED;main->last_token=1;
  iot->published=1;iot->last_token=3;iot->close_serial=4;iot->close_stage=4;
  iot->close_epoch=1;iot->close_vendor_count=2;
  close.active=close.consumed=close.retirement_module_transferred=1;
  close.reference_completed=close.synchronous_netdev_returned=1;
  close.device=&device;close.generation=2;close.open_token=3;
  close.ticket.epoch=1;close.ticket.serial=4;close.ticket.operation=WR_RADIO_BSS_CLOSE;
  open.receipt.valid=1;open.receipt.device=&device;open.receipt.epoch=1;
  open.receipt.generation=2;open.receipt.open_token=3;open.receipt.request_id[0]=1;
  probe.main_device=&main_dev;probe.iot_device=&device;probe.generation=2;
  probe.open_token=3;probe.close_serial=4;probe.ticket.epoch=1;
  probe.ticket.serial=5;probe.ticket.operation=WR_RADIO_BSS_OBSERVE;
  switch(fault){
   case 1:close.retirement_module_transferred=0;break;
   case 2:close.module_held=1;break;
   case 3:close.netdev_held=1;break;
   case 4:probe.active=1;break;
   case 5:probe.ticket.epoch++;break;
   case 6:radio.retired_serial++;break;
   case 7:producer.active=1;break;
   case 8:producer.accepting=1;break;
   case 9:request.open_token++;break;
   case 10:radio.reset_pending=1;break;
   case 11:iot->phase=WR_REF_OWNED;break;
   case 12:open.receipt.valid=0;break;
   case 13:iot->close_prior_phase++;break;
   case 14:iot->close_prior_ready++;break;
  }
  struct wr_iot_driver_close_owner prior=close;
  int result=wr_iot_driver_close_release_reference(&close,&open,&request,&radio,
    slots,2,&main_dev,&device,1,&probe,&producer,7);
  assert(result==(fault==0));
  if(fault)assert(!memcmp(&close,&prior,sizeof(close)));
  else{
   assert(!close.active);
   assert(wr_iot_driver_close_release_reference(&close,&open,&request,&radio,
     slots,2,&main_dev,&device,1,&probe,&producer,7));
   open.receipt.valid=0;
   assert(!wr_iot_driver_close_release_reference(&close,&open,&request,&radio,
     slots,2,&main_dev,&device,1,&probe,&producer,7));
  }
 }
 puts("PASS unbound release reference helper: holds/probe/epoch/producer/reset/new OPEN refusal and same-request replay; no real ioctl or no-host epoch proof");
 return 0;
}
