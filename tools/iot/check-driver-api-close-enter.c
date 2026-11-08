#include <assert.h>
#include <errno.h>
#include <string.h>
#include <stdio.h>
#include "driver-api-close-owner.h"
#include "driver-api-close-wire.h"
#include "driver-api-close-finish.h"
#include "driver-api-close-recovery.h"
#include "mbss-reaper-gate.h"
typedef int INT;typedef unsigned long ULONG;typedef void *PNET_DEV;
#define WDEV_NUM_MAX 1
static int task_identity,foreign,module_refs,dev_refs,module_available,locked;
#define current (&task_identity)
#define THIS_MODULE ((void *)0)
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);(void)(flags);assert(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);(void)(flags);assert(locked);locked=0;}while(0)
static int try_module_get(void *m){(void)m;assert(!locked);if(!module_available)return 0;module_refs++;return 1;}
static void module_put(void *m){(void)m;assert(!locked&&module_refs>0);module_refs--;}
static void dev_hold(void *d){assert(d&&!locked);dev_refs++;}
static void dev_put(void *d){assert(d&&!locked&&dev_refs>0);dev_refs--;}
struct close_test_work {int busy;};
typedef struct {
 struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[2];
 struct {struct close_test_work work;}wr_iot_mbss_work[2];
 int chip,wr_iot_transition_lock;unsigned vendor_count;
 void *net_dev;
 struct {unsigned BssidNum;struct {struct {void *if_dev;}wdev;}MBSSID[3];}ApCfg;
 struct wr_iot_driver_close_owner wr_iot_close_owner;
 struct wr_iot_driver_owner wr_iot_driver_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 unsigned wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed;
 struct {unsigned active;}wr_iot_closed_probe;
} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->chip)
#define VIRTUAL_IF_NUM(ad) ((ad)->vendor_count)
#include "driver-api-close-enter.inc"
#include "driver-api-close-finish-binding.inc"
int main(void){
 for(unsigned fault=0;fault<8;fault++){
  RTMP_ADAPTER ad={0};int main_dev,iot_dev;unsigned long seq=0;
  struct wr_iot_driver_close_request req={{1},1,2,2};
  module_refs=dev_refs=locked=0;module_available=1;
  ad.vendor_count=2;ad.chip=1;ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&seq,&iot_dev,WR_REF_FAMILY_MBSS);
  main->published=iot->published=1;main->phase=iot->phase=WR_REF_OWNED;main->last_token=1;iot->last_token=2;
  ad.wr_iot_driver_owner.receipt.device=&iot_dev;ad.wr_iot_driver_owner.receipt.epoch=1;
  ad.wr_iot_driver_owner.receipt.generation=2;ad.wr_iot_driver_owner.receipt.open_token=2;
  ad.wr_iot_driver_owner.receipt.valid=1;memcpy(ad.wr_iot_driver_owner.receipt.request_id,req.open_request_id,16);
  const void *task=current;
  switch(fault){case 1:module_available=0;break;case 2:task=&foreign;break;
   case 3:ad.chip=0;break;case 4:ad.wr_iot_control_users=1;break;
   case 5:req.open_token++;break;case 6:ad.wr_iot_closed_probe.active=1;break;
   case 7:ad.ApCfg.MBSSID[2].wdev.if_dev=&main_dev;break;}
  assert((wr_iot_driver_close_request_enter(&ad,&iot_dev,&req,task)==0)==(fault==0));
  assert(!locked);assert(module_refs==(fault==0));assert(dev_refs==(fault==0));
  if(!fault){
   assert(ad.wr_iot_close_owner.active&&ad.wr_iot_close_owner.module_held&&ad.wr_iot_close_owner.netdev_held);
   unsigned long serial=ad.wr_iot_transition.serial;
   assert(wr_iot_driver_close_request_enter(&ad,&iot_dev,&req,current)==-EBUSY);
   assert(module_refs==1&&dev_refs==1&&ad.wr_iot_transition.serial==serial);
   struct wr_iot_driver_close_owner before=ad.wr_iot_close_owner;
   assert(!wr_iot_driver_close_request_finish(&ad,&iot_dev,&foreign,0));
   assert(!memcmp(&before,&ad.wr_iot_close_owner,sizeof(before)));
   /* dev_close==0 with no consumed executor ticket is still uncertain. */
   assert(!wr_iot_driver_close_request_finish(&ad,&iot_dev,current,0));
   assert(ad.wr_iot_close_owner.active&&ad.wr_iot_close_owner.uncertain&&!ad.wr_iot_close_owner.task);
   assert(ad.wr_iot_close_owner.netdev_held&&ad.wr_iot_close_owner.module_held);
   assert(module_refs==1&&dev_refs==1);
   before=ad.wr_iot_close_owner;
   assert(!wr_iot_driver_close_request_finish(&ad,&iot_dev,current,0));
   assert(!memcmp(&before,&ad.wr_iot_close_owner,sizeof(before)));
   /* Separate completed reference state, as in actual completion fixture.
    * This is bookkeeping evidence, not physical DMA/RF completion. */
   ad.wr_iot_close_owner.task=current;ad.wr_iot_close_owner.consumed=1;
   ad.wr_iot_close_owner.uncertain=0;
   ad.wr_iot_transition.busy=0;ad.wr_iot_transition.retired_serial=serial;
   iot->phase=WR_REF_IDLE;iot->close_serial=serial;iot->close_stage=4;
   ad.vendor_count=1;
   assert(wr_iot_driver_close_request_finish(&ad,&iot_dev,current,0));
   assert(ad.wr_iot_close_owner.reference_completed&&!ad.wr_iot_close_owner.uncertain);
   assert(ad.wr_iot_close_owner.active&&!ad.wr_iot_close_owner.task);
   assert(module_refs==1&&dev_refs==1);

  }else assert(!ad.wr_iot_close_owner.active);
 }
 puts("PASS staged actual CLOSE enter: extra module/netdev holds acquired, refusals balanced, duplicate retains original owner; retirement/endpoint unbound");
 return 0;
}
