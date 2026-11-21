#include <assert.h>
#include <string.h>
#include <stdio.h>
#include "driver-api-close-recovery.h"
int main(void){
 for(unsigned fault=0;fault<9;fault++){
  struct wr_iot_driver_close_owner close={0};struct wr_iot_mbss_recovery_owner recovery;
  struct wr_iot_radio_transition radio;struct wr_iot_interface_ref slots[2]={{0}};
  int main_dev,dev;unsigned long seq=0;struct wr_iot_radio_ticket copied={0};
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(slots,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(slots,2,&seq,&dev,WR_REF_FAMILY_MBSS);
  main->published=r->published=1;main->phase=r->phase=WR_REF_OWNED;main->last_token=1;r->last_token=2;
  assert(wr_iot_radio_begin_stop(&radio,2,&close.ticket));unsigned long serial=radio.serial;
  close.active=close.uncertain=close.netdev_held=close.module_held=1;
  close.device=&dev;close.generation=2;close.open_token=2;
  r->close_epoch=close.ticket.epoch;r->close_vendor_count=2;
  r->close_prior_phase=(int)close.ticket.prior_phase;r->close_prior_ready=close.ticket.prior_ready;
  wr_iot_mbss_recovery_init(&recovery);
  switch(fault){case 1:r->generation++;break;case 2:r->close_running=1;break;
   case 3:r->removing=1;break;case 4:radio.serial++;break;case 5:close.task=&dev;break;
   case 6:close.module_held=0;break;case 7:r->phase=WR_REF_CLOSING;break;
   case 8:r->close_uncertain_reason=WR_CLOSE_UNCERTAIN_VENDOR;break;}
  struct wr_iot_driver_close_owner before=close;
  struct wr_iot_mbss_recovery_owner recovery_before=recovery;
  struct wr_iot_interface_ref record_before=*r;
  assert(wr_iot_driver_close_transfer_recovery(&close,&recovery,r,&radio)==(fault==0));
  assert(!memcmp(&record_before,r,sizeof(*r))); /* No fake CLOSING/stage. */
  if(fault){assert(!memcmp(&before,&close,sizeof(close)));assert(!memcmp(&recovery_before,&recovery,sizeof(recovery)));continue;}
  assert(close.consumed&&close.recovery_netdev_transferred&&!close.netdev_held&&close.module_held);
  assert(recovery.source==WR_MBSS_RECOVERY_RESERVED_CLOSE&&recovery.close_serial==serial&&radio.serial==serial);
  assert(wr_iot_mbss_recovery_begin(&recovery));
  assert(wr_iot_mbss_recovery_copy_close_ticket(&recovery,r,&radio,slots,2,2,&copied));
  assert(copied.serial==serial&&copied.epoch==close.ticket.epoch);
  /* Existing executor's subsequent stage2 is still the SAME operation. */
  r->phase=WR_REF_CLOSING;r->close_serial=serial;r->close_stage=2;
  assert(wr_iot_mbss_recovery_copy_close_ticket(&recovery,r,&radio,slots,2,2,&copied));
  r->close_stage=5;r->close_uncertain_reason=WR_CLOSE_UNCERTAIN_DMA;r->close_verified_stage=2;
  assert(wr_iot_mbss_recovery_record_uncertain(&recovery,r,&radio));
  assert(recovery.source==WR_MBSS_RECOVERY_UNCERTAIN);
 }
 puts("PASS reserved CLOSE recovery: same ticket, no fabricated record/stage, exact identity/refusal, continuation and uncertain provenance retained; executor/hardware not exercised");
 return 0;
}
