#include <assert.h>
#include <string.h>
#include "physical-rebind-open.h"
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
 struct wr_iot_interface_ref slots[2]={main_record,iot};
 struct wr_iot_physical_stop_terminal terminal={0};
 terminal.owner=(struct pid *)&device;terminal.request=request;
 terminal.ready=1;terminal.status=WR_STOP_RELEASED;terminal.origin=original;
 assert(wr_iot_physical_stop_origin_pair(&terminal,terminal.owner,&request,&owner,&radio,slots,2,&device,&iot_device,1));
 for(unsigned i=0;i<8;i++){
  struct wr_iot_physical_stop_terminal t=terminal;
  unsigned vendor_count=1;
  switch(i){case 0:t.ready=0;break;case 1:t.status=WR_STOP_CANCELLED;break;
   case 2:t.owner=0;break;case 3:t.request.action=WR_STOP_CANCEL;break;
   case 4:t.request.generation++;break;case 5:vendor_count=2;break;
   case 6:t.origin.main_open_token++;break;case 7:t.request.closed_serial++;break;}
  assert(!wr_iot_physical_stop_origin_pair(&t,terminal.owner,&request,&owner,&radio,slots,2,&device,&iot_device,vendor_count));
 }
 assert(!wr_iot_physical_stop_origin_pair(&terminal,(struct pid *)&iot_device,&request,&owner,&radio,slots,2,&device,&iot_device,1));
 for(unsigned i=0;i<7;i++){
  struct wr_iot_physical_stop_request q=request;
  switch(i){case 0:q.attempt++;break;case 1:q.epoch++;break;
   case 2:q.generation++;break;case 3:q.open_token++;break;
   case 4:q.closed_serial++;break;case 5:q.nonce[15]++;break;
   case 6:q.action=WR_STOP_CANCEL;break;}
  assert(!wr_iot_physical_stop_origin_pair(&terminal,terminal.owner,&q,&owner,&radio,slots,2,&device,&iot_device,1));
 }
 assert(!wr_iot_physical_stop_origin_pair(&terminal,terminal.owner,&request,&owner,&radio,0,2,&device,&iot_device,1));
 assert(!wr_iot_physical_stop_origin_pair(&terminal,terminal.owner,&request,&owner,&radio,slots,0,&device,&iot_device,1));
 assert(slots[1].close_epoch==5&&radio.epoch==7);
 for(unsigned fault=0;fault<7;fault++){
  struct wr_iot_physical_rebind_probe probe={0};
  struct wr_iot_radio_transition r=radio;
  struct wr_iot_interface_ref records[2]={slots[0],slots[1]};
  assert(wr_iot_physical_rebind_probe_begin(&probe,&terminal,terminal.owner,&request,&owner,&r,records,2,&device,&iot_device,1));
  assert(!wr_iot_physical_rebind_probe_begin(&probe,&terminal,terminal.owner,&request,&owner,&r,records,2,&device,&iot_device,1));
  struct wr_iot_physical_stop_terminal t=terminal;
  struct wr_iot_physical_stop_request q=request;
  if(fault==5){q.nonce[0]++;t.request=q;}
  if(fault==6){q.attempt++;t.request=q;}
  if(fault==1)r.epoch++;
  if(fault==2)records[0].last_token++;
  if(fault==3)records[1].close_serial++;
  assert(wr_iot_physical_rebind_probe_finish(&probe,&t,terminal.owner,&q,&owner,&r,records,2,&device,&iot_device,1,fault==4?0:1)==(fault==0));
  assert(!probe.active&&!r.busy&&records[1].close_epoch==5);
  if(!fault){
   unsigned char open_id[16]={9},empty_id[16]={0};
   assert(!wr_iot_physical_rebind_claim(&probe,&t,terminal.owner,&q,&owner,&r,records,2,&device,&iot_device,1,empty_id));
   assert(probe.accepted&&!probe.spent);
   r.serial++;r.retired_serial++;
   assert(!wr_iot_physical_rebind_claim(&probe,&t,terminal.owner,&q,&owner,&r,records,2,&device,&iot_device,1,open_id));
   r.serial--;r.retired_serial--;
   assert(wr_iot_physical_rebind_claim(&probe,&t,terminal.owner,&q,&owner,&r,records,2,&device,&iot_device,1,open_id));
   assert(probe.spent&&!probe.accepted&&probe.open_request_id[0]==9);
   assert(!wr_iot_physical_rebind_claim(&probe,&t,terminal.owner,&q,&owner,&r,records,2,&device,&iot_device,1,open_id));
   assert(!wr_iot_physical_rebind_probe_begin(&probe,&t,terminal.owner,&q,&owner,&r,records,2,&device,&iot_device,1));
  }

  assert(!wr_iot_physical_rebind_probe_finish(&probe,&t,terminal.owner,&q,&owner,&r,records,2,&device,&iot_device,1,1));
 }
 {
  struct wr_iot_physical_rebind_probe probe={0};
  struct wr_iot_radio_transition r=radio;
  struct wr_iot_interface_ref records[2]={slots[0],slots[1]};
  struct wr_iot_driver_owner opened={0};int task;
  struct wr_iot_driver_open_request open_request={.adapter_epoch=7,.device_generation=3,.request_id={8}};
  assert(wr_iot_physical_rebind_probe_begin(&probe,&terminal,terminal.owner,&request,&owner,&r,records,2,&device,&iot_device,1));
  assert(wr_iot_physical_rebind_probe_finish(&probe,&terminal,terminal.owner,&request,&owner,&r,records,2,&device,&iot_device,1,1));
  assert(wr_iot_driver_owner_query(&opened,open_request.request_id,7,3));
  assert(!wr_iot_physical_rebind_open_reserve(&probe,&terminal,terminal.owner,&request,&owner,&opened,&r,records,2,&device,&iot_device,1,&task,&open_request,1,0));
  assert(!probe.spent&&probe.accepted&&!opened.active);
  assert(wr_iot_physical_rebind_open_reserve(&probe,&terminal,terminal.owner,&request,&owner,&opened,&r,records,2,&device,&iot_device,1,&task,&open_request,0,0));
  assert(probe.spent&&opened.active&&r.busy==WR_RADIO_BSS_OPEN&&records[1].phase==WR_REF_RESERVED);
  assert(!wr_iot_physical_rebind_open_reserve(&probe,&terminal,terminal.owner,&request,&owner,&opened,&r,records,2,&device,&iot_device,1,&task,&open_request,0,0));
  assert(wr_iot_driver_owner_leave(&opened,&task,&iot_device,&r,records,2));
  assert(!opened.active&&!r.busy&&probe.spent); /* Pre-mutation cancellation never refunds handoff. */
 }
 return 0;
}
