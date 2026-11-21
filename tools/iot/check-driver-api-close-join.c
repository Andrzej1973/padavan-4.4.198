#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-join.h"
int main(void){
 for(unsigned fault=0;fault<16;fault++){
  int dev;struct wr_iot_driver_close_owner close={0};
  struct wr_iot_mbss_recovery_owner recovery={0};struct wr_iot_interface_ref record={0};
  struct wr_iot_driver_close_join_receipt receipt={0};int joined=1;
  close.active=close.consumed=close.module_held=close.recovery_netdev_transferred=1;
  close.device=&dev;close.generation=2;close.open_token=3;
  close.ticket.epoch=1;close.ticket.serial=4;close.ticket.operation=WR_RADIO_BSS_CLOSE;
  close.ticket.prior_phase=WR_RADIO_READY;close.ticket.prior_ready=1;
  recovery.device=&dev;recovery.generation=2;recovery.open_token=3;recovery.close_serial=4;
  recovery.close_ticket=close.ticket;recovery.close_ticket_valid=1;
  recovery.phase=WR_MBSS_OWNER_RUNNING;recovery.completed=recovery.deferred_owners=1;
  record.device=&dev;record.generation=2;record.last_token=3;record.published=1;
  record.family=WR_REF_FAMILY_MBSS;record.phase=WR_REF_IDLE;record.close_stage=4;
  record.close_epoch=1;record.close_serial=4;record.close_vendor_count=2;
  record.close_prior_phase=WR_RADIO_READY;record.close_prior_ready=1;
  switch(fault){case 1:joined=0;break;case 2:recovery.completed=0;break;
   case 3:record.generation++;break;case 4:recovery.close_ticket.epoch++;break;
   case 5:close.task=&dev;break;case 6:close.netdev_held=1;break;
   case 7:close.module_held=0;break;case 8:record.removal_stage=1;break;
   case 9:record.close_running=1;break;case 10:recovery.close_ticket.prior_ready=0;break;
   case 11:close.recovery_netdev_returned=1;break;
   case 12:record.close_uncertain_reason=1;break;case 13:recovery.close_serial++;break;
   case 14:close.synchronous_put_pending=1;break;case 15:close.synchronous_netdev_returned=1;break;}
  struct wr_iot_driver_close_owner before=close;
  assert(!wr_iot_driver_close_join_returned(&close,&receipt));
  assert(wr_iot_driver_close_join_claim(&close,&recovery,&record,joined,&receipt)==(fault==0));
  if(fault){assert(!memcmp(&before,&close,sizeof(close)));continue;}
  assert(close.recovery_join_pending&&!close.recovery_netdev_returned);
  assert(!wr_iot_driver_close_join_claim(&close,&recovery,&record,1,&receipt));
  assert(wr_iot_mbss_recovery_complete(&recovery,1));
  struct wr_iot_driver_close_join_receipt wrong=receipt;wrong.serial++;
  assert(!wr_iot_driver_close_join_returned(&close,&wrong));
  /* Simulated dev_put completion boundary; kernel binding is not installed. */
  assert(wr_iot_driver_close_join_returned(&close,&receipt));
  assert(close.active&&close.module_held&&close.recovery_netdev_returned&&!close.recovery_join_pending);
  assert(!wr_iot_driver_close_join_returned(&close,&receipt));
 }
 puts("PASS exact join receipt: original identity survives recovery reset; no return before claim, drift/duplicate refusal; module/API owner retained, dev_put binding absent");
 return 0;
}
