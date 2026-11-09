#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-owner.h"
#include "mbss-closed-probe.h"
int main(void){
 for(unsigned fault=0;fault<10;fault++){
  struct wr_iot_driver_owner o={0};struct wr_iot_radio_transition r;
  struct wr_iot_interface_ref slots[2]={{0}},*main_ref,*iot_ref;
  int main_dev=0,iot_dev=0,task=0;unsigned long sequence=0;
  struct wr_iot_driver_open_request q={.ssid_length=3,.password_length=8};
  memcpy(q.ssid,"IoT",3);memcpy(q.password,"password",8);q.request_id[0]=1;
  wr_iot_radio_transition_init(&r);r.phase=WR_RADIO_READY;r.main_ready=1;
  main_ref=wr_iot_registry_add_family(slots,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  iot_ref=wr_iot_registry_add_family(slots,2,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
  main_ref->published=iot_ref->published=1;main_ref->phase=WR_REF_OWNED;main_ref->last_token=1;
  r.serial=r.retired_serial=1;
  q.adapter_epoch=r.epoch;q.device_generation=iot_ref->generation;
  assert(wr_iot_driver_owner_query(&o,q.request_id,q.adapter_epoch,q.device_generation));
  o.receipt.valid=o.refusal.valid=1;o.receipt.first_beacon_confirmed=1;o.mutation_started=1;
  assert(wr_iot_driver_owner_reserve(&o,&r,slots,2,&main_dev,&iot_dev,1,&task,&q,0,0));
  /* Accepted reservation invalidates all history from a preceding attempt. */
  assert(!o.receipt.valid&&!o.refusal.valid&&!o.mutation_started&&!o.receipt.first_beacon_confirmed);
  assert(wr_iot_driver_owner_take(&o,&task,&iot_dev,&r,slots,2));
  unsigned long token=o.ticket.serial;
  o.mutation_started=(fault!=1&&fault!=9);
  int acquired=fault!=1&&fault!=8&&fault!=9;
  assert(wr_iot_ref_open_finish(iot_ref,&iot_dev,iot_ref->generation,token,acquired));
  if(fault==9)iot_ref->open_unmutated=0;
  if(!acquired)assert(wr_iot_radio_abort_bss_open_unmutated(&r,&o.ticket));
  else assert(wr_iot_radio_finish(&r,&o.ticket,1));
  if(fault==2)r.reset_pending=1;
  assert(wr_iot_driver_owner_leave(&o,&task,&iot_dev,&r,slots,2)==(fault!=2));
  assert(!o.request.password[0]&&!o.task);
  for(unsigned j=0;j<16;j++)assert(o.uncertain_request_id[j]==(fault==2?q.request_id[j]:0));

  if(fault==1||fault==2||fault==8||fault==9){
   assert(!o.receipt.valid);assert(o.refusal.valid==(fault==1));
   assert(wr_iot_driver_refusal_matches(&o,q.request_id,&iot_dev,q.adapter_epoch,q.device_generation,token)==(fault==1));
   q.request_id[0]^=2;assert(!wr_iot_driver_refusal_matches(&o,q.request_id,&iot_dev,q.adapter_epoch,q.device_generation,token));
   continue;
  }
  assert(o.receipt.valid&&!o.receipt.first_beacon_confirmed);
  unsigned char id[16];memcpy(id,q.request_id,16);
  unsigned long epoch=r.epoch,generation=iot_ref->generation;
  if(fault==3)id[0]^=1;
  if(fault==4)epoch++;
  if(fault==5)generation++;
  if(fault==6)token++;
  if(fault==7)o.active=1;
  assert(wr_iot_driver_open_receipt_matches(&o,id,&iot_dev,epoch,generation,token)==(fault==0));
  if(fault)continue;
  struct wr_iot_radio_ticket close;
  assert(wr_iot_radio_begin_stop(&r,2,&close));
  assert(wr_iot_ref_begin_close(iot_ref,&iot_dev,generation,token));
  iot_ref->close_epoch=close.epoch;iot_ref->close_vendor_count=2;iot_ref->close_serial=close.serial;
  assert(wr_iot_ref_consume(iot_ref,&iot_dev,generation,token));iot_ref->close_stage=4;
  assert(wr_iot_radio_finish(&r,&close,1));
  assert(wr_iot_driver_open_receipt_matches(&o,id,&iot_dev,epoch,generation,token));
  struct wr_iot_mbss_closed_probe probe={0};
  assert(wr_iot_mbss_closed_probe_begin(&probe,&r,slots,2,&main_dev,&iot_dev,generation,token,close.serial,1));
  assert(wr_iot_mbss_closed_probe_finish(&probe,&r,slots,2,1,1));
  struct wr_iot_driver_owner reconstructed={0};
  assert(!wr_iot_driver_open_receipt_matches(&reconstructed,id,&iot_dev,epoch,generation,token));
 }
 puts("PASS successful OPEN receipt: exact nonsecret transaction/epoch/netdev/token, no receipt for unmutated/uncertain OPEN, CLOSED local history composition and fresh-owner refusal. No RF acceptance.");return 0;
}
