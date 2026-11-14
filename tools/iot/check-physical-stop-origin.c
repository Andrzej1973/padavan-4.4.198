#include <assert.h>
#include <string.h>
#include "physical-stop-origin.h"
int main(void)
{
 int device;
 struct wr_iot_physical_stop_origin original={.main_generation=2,.main_open_token=3,
  .arm_epoch=5,.ticket_serial=7,.ticket_epoch=6,.completion_epoch=6,.valid=1};
 struct wr_iot_main_recovery_release_receipt receipt={.device=&device,.generation=2,
  .open_token=3,.close_serial=9,.ticket={.serial=7,.epoch=6,.operation=WR_RADIO_CLOSE},
  .completion_epoch=6,.valid=1};
 assert(wr_iot_physical_stop_origin_matches(&original,&receipt));
 assert(!wr_iot_physical_stop_origin_matches(0,&receipt));
 assert(!wr_iot_physical_stop_origin_matches(&original,0));
 for(unsigned i=0;i<14;i++){
  struct wr_iot_physical_stop_origin s=original;
  struct wr_iot_main_recovery_release_receipt r=receipt;
  switch(i){
   case 0:s.valid=0;break;case 1:r.valid=0;break;case 2:r.device=0;break;
   case 3:s.main_generation++;break;case 4:s.main_open_token++;break;
   case 5:s.ticket_serial++;break;case 6:s.ticket_epoch++;break;
   case 7:s.completion_epoch++;break;case 8:r.close_serial=0;break;
   case 9:r.ticket.operation=WR_RADIO_START;break;case 10:r.ticket.reset_kind=1;break;
   case 11:s.arm_epoch=s.ticket_epoch;break;case 12:s.main_generation=0;r.generation=0;break;
   case 13:s.completion_epoch=5;r.completion_epoch=5;break;
  }
  struct wr_iot_physical_stop_origin before=s;
  struct wr_iot_main_recovery_release_receipt old=r;
  assert(!wr_iot_physical_stop_origin_matches(&s,&r));
  assert(!memcmp(&s,&before,sizeof(s))&&!memcmp(&r,&old,sizeof(r)));
 }
 struct wr_iot_main_recovery_owner owner={0};owner.last_release=receipt;
 struct wr_iot_radio_transition radio={0};
 radio.epoch=7;radio.serial=8;radio.retired_serial=8;
 radio.phase=WR_RADIO_READY;radio.main_ready=1;
 struct wr_iot_interface_ref main_record={0};
 main_record.device=&device;main_record.generation=2;main_record.last_token=4;
 main_record.published=1;main_record.phase=WR_REF_OWNED;main_record.family=WR_REF_FAMILY_MAIN;
 assert(wr_iot_physical_stop_origin_main_ready(&original,&owner,&radio,&main_record));
 for(unsigned i=0;i<18;i++){
  struct wr_iot_main_recovery_owner o=owner;
  struct wr_iot_radio_transition r=radio;
  struct wr_iot_interface_ref m=main_record;
  switch(i){
   case 0:r.epoch=6;break;case 1:r.serial=7;r.retired_serial=7;break;
   case 2:r.retired_serial--;break;case 3:r.active_tx=1;break;
   case 4:r.reset_pending=1;break;case 5:r.pm_suspended=1;break;
   case 6:r.main_ready=0;break;case 7:r.phase=WR_RADIO_UNVERIFIED;break;
   case 8:o.deferred_owners=1;break;case 9:o.netdev_release_started=1;break;
   case 10:o.device=&device;break;case 11:m.generation++;break;
   case 12:m.last_token=3;break;case 13:m.removing=1;break;
   case 14:m.close_running=1;break;case 15:m.phase=WR_REF_IDLE;break;
   case 16:m.family=WR_REF_FAMILY_MBSS;break;case 17:m.published=0;break;
  }
  assert(!wr_iot_physical_stop_origin_main_ready(&original,&o,&r,&m));
 }
 struct wr_iot_physical_stop_request request={.action=WR_STOP_RELEASE,.epoch=5,
  .generation=3,.open_token=9,.closed_serial=10,.attempt=12,.nonce={1}};
 int iot_device;
 struct wr_iot_interface_ref iot={0};iot.device=&iot_device;
 iot.family=WR_REF_FAMILY_MBSS;iot.published=1;iot.phase=WR_REF_IDLE;
 iot.generation=3;iot.last_token=9;iot.close_serial=10;iot.close_epoch=5;iot.close_stage=4;
 assert(wr_iot_physical_stop_origin_iot_history(&request,&iot,&iot_device));
 for(unsigned i=0;i<12;i++){
  struct wr_iot_interface_ref r=iot;
  struct wr_iot_physical_stop_request q=request;
  switch(i){
   case 0:r.generation++;break;case 1:r.last_token++;break;
   case 2:r.close_serial++;break;case 3:r.close_epoch++;break;
   case 4:r.phase=WR_REF_OWNED;break;case 5:r.close_running=1;break;
   case 6:r.close_stage=3;break;case 7:r.removing=1;break;
   case 8:r.family=WR_REF_FAMILY_MAIN;break;case 9:r.open_unmutated=1;break;
   case 10:q.action=WR_STOP_CANCEL;break;case 11:r.device=&device;break;
  }
  assert(!wr_iot_physical_stop_origin_iot_history(&q,&r,&iot_device));
 }
 return 0;
}
