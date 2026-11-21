#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-progress-match.h"
int main(void){
 for(unsigned fault=0;fault<15;fault++){
  int dev,other;const void *target=&dev;
  struct wr_iot_driver_close_owner close={0};struct wr_iot_driver_owner open={0};
  struct wr_iot_driver_close_request request={{1},1,2,3};
  close.active=1;close.device=&dev;close.generation=2;close.open_token=3;
  close.ticket.epoch=1;close.ticket.serial=4;close.ticket.operation=WR_RADIO_BSS_CLOSE;
  open.receipt.valid=1;open.receipt.device=&dev;open.receipt.epoch=1;
  open.receipt.generation=2;open.receipt.open_token=3;open.receipt.request_id[0]=1;
  switch(fault){
   case 1:close.active=0;break;case 2:target=&other;break;
   case 3:request.open_request_id[15]=1;break;case 4:request.adapter_epoch++;break;
   case 5:request.device_generation++;break;case 6:request.open_token++;break;
   case 7:request.adapter_epoch|=1ULL<<32;break;
   case 8:request.device_generation|=1ULL<<32;break;
   case 9:request.open_token|=1ULL<<32;break;
   case 10:open.receipt.valid=0;break;case 11:close.task=&other;break;
   case 12:close.ticket.operation=WR_RADIO_CLOSE;break;
   case 13:close.ticket.reset_kind=1;break;case 14:open.poisoned=1;break;
  }
  struct wr_iot_driver_close_owner before=close;struct wr_iot_driver_owner prior=open;
  assert(wr_iot_driver_close_progress_matches(&close,&open,target,&request)==(fault==0));
  assert(!memcmp(&before,&close,sizeof(close))&&!memcmp(&prior,&open,sizeof(open)));
 }
 puts("PASS CLOSE progress identity: nonce/device/epoch/generation/token, no 64-bit truncation, active-task/reset/poison refusal; read-only predicate, no endpoint");
}
