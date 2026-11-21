#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-recovery.h"
int main(void){
 for(unsigned fault=0;fault<16;fault++){
  struct wr_iot_radio_transition radio;struct wr_iot_driver_close_owner close={0};
  struct wr_iot_mbss_recovery_owner recovery;struct wr_iot_interface_ref record={0};int dev;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  wr_iot_mbss_recovery_init(&recovery);
  assert(wr_iot_radio_begin_stop(&radio,2,&close.ticket));
  close.active=close.consumed=close.uncertain=1;close.device=&dev;close.generation=2;close.open_token=3;
  record.device=&dev;record.generation=2;record.last_token=3;record.published=1;
  record.family=WR_REF_FAMILY_MBSS;record.phase=WR_REF_CLOSING;
  record.close_stage=2;record.close_serial=close.ticket.serial;
  record.close_epoch=close.ticket.epoch;record.close_vendor_count=2;
  record.close_prior_phase=(int)close.ticket.prior_phase;record.close_prior_ready=close.ticket.prior_ready;
  int netdev=1,module=1,fence=1;
  switch(fault){case 1:netdev=0;break;case 2:module=0;break;case 3:fence=0;break;
   case 4:record.close_stage=0;break;case 5:record.generation++;break;
   case 6:record.close_serial++;break;case 7:record.close_stage=4;record.phase=WR_REF_IDLE;break;
   case 8:record.close_stage=5;record.close_uncertain_reason=WR_CLOSE_UNCERTAIN_CR;record.close_verified_stage=0;break;
   case 9:record.close_stage=5;record.close_uncertain_reason=WR_CLOSE_UNCERTAIN_CR;record.close_verified_stage=3;break;
   case 10:record.close_running=1;break;
   case 11:record.removal_stage=1;break;
   case 12:record.removing=1;break;
   case 13:close.task=&dev;break;
   case 14:close.reference_completed=1;break;
   case 15:close.consumed=0;break;
  }
  struct wr_iot_driver_close_owner before=close;
  struct wr_iot_mbss_recovery_owner recovery_before=recovery;
  struct wr_iot_interface_ref record_before=record;
  struct wr_iot_radio_transition radio_before=radio;
  assert(wr_iot_driver_close_queue_recovery(&close,&recovery,&record,&radio,netdev,module,fence)==(fault==0||fault==8));
  assert(!memcmp(&before,&close,sizeof(close)));
  assert(!memcmp(&record_before,&record,sizeof(record)));
  assert(!memcmp(&radio_before,&radio,sizeof(radio)));
  if(fault!=0&&fault!=8)assert(!memcmp(&recovery_before,&recovery,sizeof(recovery)));
  if(fault==0||fault==8){assert(recovery.device==&dev&&recovery.generation==2&&recovery.open_token==3);assert(recovery.close_ticket.serial==close.ticket.serial);}
  wr_iot_mbss_recovery_init(&recovery);
  close.netdev_held=netdev;close.module_held=module;
  /* Explicit fence refusal has already been tested above; an active API
   * owner itself participates in the composed adapter lifetime fence. */
  if(fault!=3){
   before=close;recovery_before=recovery;
   int accepted=wr_iot_driver_close_transfer_recovery(&close,&recovery,&record,&radio);
   assert(accepted==(fault==0||fault==8));
   if(accepted){
    assert(!close.netdev_held&&close.recovery_netdev_transferred&&close.module_held&&close.active);
    struct wr_iot_driver_close_owner transferred=close;
    struct wr_iot_mbss_recovery_owner queued=recovery;
    assert(!wr_iot_driver_close_transfer_recovery(&close,&recovery,&record,&radio));
    assert(!memcmp(&transferred,&close,sizeof(close))&&!memcmp(&queued,&recovery,sizeof(recovery)));
   }else assert(!memcmp(&before,&close,sizeof(close))&&!memcmp(&recovery_before,&recovery,sizeof(recovery)));
  }

 }
 puts("PASS real MBSS recovery queue handoff: exact ticket retained, actual pin preconditions required, unsupported stages/refused identity fail; kernel pin acquisition/scheduling unbound");
}
