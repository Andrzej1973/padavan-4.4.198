#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-synchronous-put.h"
typedef int INT;typedef unsigned long ULONG;typedef int *PNET_DEV;
#define WDEV_NUM_MAX 1
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
typedef struct {
 int wr_iot_transition_lock;unsigned count;PNET_DEV net_dev;
 struct wr_iot_driver_close_owner wr_iot_close_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
} RTMP_ADAPTER;
static int locked,rtnl,put_calls,drift;static RTMP_ADAPTER *current_ad;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(locked);locked=0;}while(0)
static int rtnl_is_locked(void){return rtnl;}
static void dev_put(PNET_DEV dev){
 assert(rtnl&&!locked&&dev==current_ad->wr_iot_close_owner.device);
 assert(current_ad->wr_iot_close_owner.active&&current_ad->wr_iot_close_owner.module_held);
 assert(current_ad->wr_iot_close_owner.synchronous_put_pending&&!current_ad->wr_iot_close_owner.synchronous_netdev_returned);
 assert(!current_ad->wr_iot_close_owner.netdev_held);put_calls++;
 if(drift)current_ad->wr_iot_close_owner.generation++;
}
#include "driver-api-close-synchronous-put.inc"
static int task_identity;
#define current (&task_identity)
#include "driver-api-close-finish.h"
#include "driver-api-close-finish-binding.inc"
static int wr_iot_driver_close_recovery_submit(RTMP_ADAPTER *ad,PNET_DEV dev){(void)ad;(void)dev;assert(!"completed synchronous CLOSE entered recovery");return -1;}
static int wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad){(void)ad;assert(!"completed synchronous CLOSE scheduled poll");return -1;}
#include "driver-api-close-finish-recovery.inc"
int main(void){
 for(unsigned fault=0;fault<15;fault++){
  RTMP_ADAPTER ad={0};int main_dev,dev,other;unsigned long sequence=0;
  ad.count=1;ad.net_dev=&main_dev;current_ad=&ad;rtnl=1;put_calls=drift=locked=0;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);
  ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  ad.wr_iot_transition.serial=ad.wr_iot_transition.retired_serial=3;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *record=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&sequence,&dev,WR_REF_FAMILY_MBSS);
  main->published=record->published=1;main->phase=WR_REF_OWNED;main->last_token=1;record->last_token=2;
  record->close_epoch=1;record->close_serial=3;record->close_vendor_count=2;
  record->close_prior_phase=WR_RADIO_READY;record->close_prior_ready=1;record->close_stage=4;
  struct wr_iot_driver_close_owner *c=&ad.wr_iot_close_owner;
  c->active=c->consumed=c->reference_completed=c->module_held=c->netdev_held=1;
  c->device=&dev;c->generation=2;c->open_token=2;
  c->ticket.epoch=1;c->ticket.serial=3;c->ticket.operation=WR_RADIO_BSS_CLOSE;
  c->ticket.prior_phase=WR_RADIO_READY;c->ticket.prior_ready=1;
  switch(fault){
   case 1:c->module_held=0;break;case 2:c->netdev_held=0;break;
   case 3:c->reference_completed=0;break;case 4:c->uncertain=1;break;
   case 5:c->generation++;break;case 6:record->close_stage=3;break;
   case 7:c->task=&other;break;case 8:c->recovery_netdev_transferred=1;break;
   case 9:rtnl=0;break;case 10:break;case 11:drift=1;break;
   case 12:c->retirement_started=1;break;case 13:c->retirement_entered=1;break;
   case 14:c->retirement_canceling=1;break;
  }
  struct wr_iot_driver_close_owner before=*c;
  int status=wr_iot_driver_close_synchronous_put(&ad,fault==10?&other:&dev);
  assert(status==(fault==0?0:fault==11?-EUCLEAN:-EBUSY));assert(!locked);
  if(fault&&fault!=11){assert(!put_calls&&!memcmp(&before,c,sizeof(before)));continue;}
  assert(put_calls==1&&c->active&&c->module_held&&!c->netdev_held&&!c->recovery_netdev_transferred);
  assert(c->synchronous_netdev_returned==(fault==0)&&c->synchronous_put_pending==(fault==11));
  assert(wr_iot_driver_close_netdev_return_complete(c)==(fault==0));
  assert(wr_iot_driver_close_synchronous_put(&ad,&dev)==-EBUSY&&put_calls==1);
  assert(wr_iot_driver_close_blocks_adapter_retirement(c));
  if(!fault){
   *c=before;c->reference_completed=0;c->task=current;put_calls=0;
   int handoff=99;
   assert(wr_iot_driver_close_finish_recover(&ad,&dev,current,0,&handoff));
   assert(handoff==-1&&put_calls==1&&c->synchronous_netdev_returned&&!c->task);
   assert(c->module_held&&c->active&&!c->recovery_netdev_transferred);
   assert(!wr_iot_driver_close_finish_recover(&ad,&dev,current,0,&handoff)&&put_calls==1);
   *c=before;c->reference_completed=0;c->task=current;put_calls=0;drift=1;
   assert(!wr_iot_driver_close_finish_recover(&ad,&dev,current,0,&handoff));
   assert(put_calls==1&&c->synchronous_put_pending&&!c->synchronous_netdev_returned);
   assert(c->active&&c->module_held&&!c->netdev_held);
   assert(!wr_iot_driver_close_finish_recover(&ad,&dev,current,0,&handoff)&&put_calls==1);
  }
 }
 puts("PASS synchronous netdev return: actual binding claim/dev_put/ack, duplicate no second put, drift retains pending, RTNL/identity/provenance refusals retain owner; device calls mocked");
}
