/* Composes actual synchronous finish, stopped create, wake and fixed body.
 * Only kernel scheduling/reference primitives are injected. No RF acceptance. */
#define WR_CLOSE_LAUNCH_TEST
#define WR_CLOSE_DYNAMIC_CURRENT_TEST
#define WR_CLOSE_THREAD_BODY_TEST
#define WR_CLOSE_THREAD_ENTRY_TEST
#define WR_CLOSE_START_BINDING_TEST
#define WR_CLOSE_CREATE_BINDING_TEST
#define WR_CLOSE_KERNEL_BINDING_TEST
#define main retirement_regressions
#include "check-driver-api-close-retirement.c"
#undef main
#include "driver-api-close-retirement-launch.inc"
static int task_locked,reconcile_drift;
static void task_lock(struct task_struct *task){assert(task&&!test_locked&&!task_locked);task_locked=1;}
static void task_unlock(struct task_struct *task){assert(task&&task_locked);task_locked=0;if(reconcile_drift){launch_ad->wr_iot_close_owner.generation++;reconcile_drift=0;}}
#include "driver-api-close-retirement-reconcile.inc"
typedef void *PNET_DEV;
#include "driver-api-close-synchronous-put.h"
static int chain_puts;
static void dev_put(PNET_DEV dev){
 assert(rtnl_held&&!test_locked&&dev==create_ad->wr_iot_close_owner.device);
 assert(create_ad->wr_iot_close_owner.synchronous_put_pending);
 assert(create_ad->wr_iot_close_owner.active&&create_ad->wr_iot_close_owner.module_held);
 chain_puts++;
}
#include "driver-api-close-synchronous-put.inc"
#include "driver-api-close-finish.h"
#include "driver-api-close-finish-binding.inc"
static int wr_iot_driver_close_recovery_submit(RTMP_ADAPTER *ad,PNET_DEV dev){(void)ad;(void)dev;assert(!"synchronous chain queued recovery");return -1;}
static int wr_iot_mbss_poll_schedule(RTMP_ADAPTER *ad){(void)ad;assert(!"synchronous chain scheduled poll");return -1;}
#include "driver-api-close-finish-recovery.inc"
#include "driver-api-close-progress-match.h"
#include "driver-api-close-progress.inc"
#include "driver-api-close-progress-wire.h"
#include "driver-api-close-progress-entry.inc"
struct ifreq {void *ifr_data;};
struct progress_namespace {void *user_ns;};
static struct progress_namespace progress_ns;
static int progress_capable=1,progress_copy_fault,progress_copies;
#define CAP_NET_ADMIN 12
static struct progress_namespace *dev_net(PNET_DEV dev){assert(dev);return &progress_ns;}
static int ns_capable(void *ns,int cap){assert(ns==progress_ns.user_ns&&cap==12);return progress_capable;}
static int copy_from_user(void *to,const void *from,unsigned long n){assert(!test_locked&&n==64);progress_copies++;if(progress_copy_fault)return 1;memcpy(to,from,n);return 0;}
#include "driver-api-close-progress-ioctl.inc"
int main(void){
 retirement_regressions();
 static RTMP_ADAPTER ad;int dev,main_dev;unsigned long sequence=0;
 ad.chip=1;ad.count=1;ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
 wr_iot_radio_transition_init(&ad.wr_iot_transition);
 ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
 ad.wr_iot_transition.serial=ad.wr_iot_transition.retired_serial=3;
 wr_iot_mbss_poll_init(&ad.wr_iot_mbss_poll_state);wr_iot_mbss_reaper_gate_init(&ad.wr_iot_mbss_reaper_gate);
 for(unsigned i=0;i<2;i++)wr_iot_mbss_recovery_init(&ad.wr_iot_mbss_recovery[i]);
 struct wr_iot_interface_ref *main=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
 struct wr_iot_interface_ref *record=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&sequence,&dev,WR_REF_FAMILY_MBSS);
 main->published=record->published=1;main->phase=WR_REF_OWNED;main->last_token=1;record->last_token=2;
 record->close_epoch=1;record->close_serial=3;record->close_vendor_count=2;
 record->close_prior_phase=WR_RADIO_READY;record->close_prior_ready=1;record->close_stage=4;
 struct wr_iot_driver_close_owner *c=&ad.wr_iot_close_owner;
 c->active=c->consumed=c->module_held=c->netdev_held=1;c->task=current;c->device=&dev;
 c->generation=2;c->open_token=2;c->ticket.epoch=1;c->ticket.serial=3;
 c->ticket.operation=WR_RADIO_BSS_CLOSE;c->ticket.prior_phase=WR_RADIO_READY;c->ticket.prior_ready=1;
 RTMP_ADAPTER pristine=ad;
 for(unsigned scenario=0;scenario<8;scenario++){
 ad=pristine;
 create_ad=&ad;chain_puts=exit_calls=wake_calls=0;create_mode=0;wake_accept=rtnl_held=1;body_rtnl=0;
 stop_calls=0;stop_result=-EINTR;stop_drift=0;launch_ad=&ad;launch_drift=0;create_calls=0;
 int handoff=99;
 assert(wr_iot_driver_close_finish_recover(&ad,&dev,current,0,&handoff));
 assert(handoff==-1&&chain_puts==1&&c->synchronous_netdev_returned&&!c->task);
 assert(c->active&&c->module_held&&wr_iot_driver_close_blocks_adapter_retirement(c));
 struct task_struct *handle=0;
 if(scenario==3)rtnl_held=0;
 if(scenario==4)create_mode=1;
 if(scenario==5)wake_accept=0;
 if(scenario==6)create_mode=2;
 if(scenario==7)launch_drift=1;
 struct wr_iot_driver_close_request progress={{1},1,2,2};
 ad.wr_iot_driver_owner.receipt.valid=1;ad.wr_iot_driver_owner.receipt.device=&dev;
 ad.wr_iot_driver_owner.receipt.epoch=1;ad.wr_iot_driver_owner.receipt.generation=2;
 ad.wr_iot_driver_owner.receipt.open_token=2;ad.wr_iot_driver_owner.receipt.request_id[0]=1;
 if(!scenario){
  progress.open_token++;
  assert(wr_iot_driver_close_progress(&ad,&dev,&progress)==-EBUSY&&!create_calls);
  progress.open_token--;
 }
 unsigned char progress_wire[64];
 assert(wr_iot_driver_close_request_encode(progress_wire,64,&progress));
 assert(wr_iot_driver_close_progress_reply(&ad,&dev,progress_wire)==-EINVAL&&!create_calls);
 assert(wr_iot_driver_close_progress_encode(progress_wire,64,&progress));
 struct ifreq progress_rq={progress_wire};
 progress_capable=0;progress_copies=0;
 assert(wr_iot_driver_close_progress_ioctl(&ad,&dev,&progress_rq)==(rtnl_held?-EPERM:-EBUSY));
 assert(!progress_copies&&!create_calls);progress_capable=1;
 if(rtnl_held){
  progress_copy_fault=1;
  assert(wr_iot_driver_close_progress_ioctl(&ad,&dev,&progress_rq)==-EFAULT&&!create_calls);
  progress_copy_fault=0;
 }
 int launch_status=wr_iot_driver_close_progress_ioctl(&ad,&dev,&progress_rq);
 handle=(struct task_struct *)c->retirement_handle;
 if(launch_status==-EINPROGRESS)launch_status=0;
 if(scenario>=3){
  assert(launch_status==(scenario==4?-12:scenario==5?-EUCLEAN:-EBUSY));
  assert(c->active&&c->module_held&&chain_puts==1&&!exit_calls);
  if(scenario==5){
   assert(handle==&stopped_task&&handle->refs==2&&c->retirement_started&&!stop_calls);
   assert(wr_iot_driver_close_retirement_launch(&ad,&handle)==-EINVAL&&handle==&stopped_task);
   assert(wr_iot_driver_close_retirement_cancel(&ad,&handle)==-EBUSY&&!stop_calls);
   assert(c->retirement_handle==handle);
   /* Retained caller ref prevents thread module handoff even if task runs. */
   rtnl_held=0;test_current=&stopped_task;stopped_task.flags=PF_KTHREAD;
   assert(wr_iot_driver_close_retirement_thread(&ad)==-EBUSY);
   test_current=&creator_task;rtnl_held=1;
   assert(c->retirement_handle==handle&&!c->retirement_task&&c->module_held&&!exit_calls);
   struct task_struct *another=0;int prior_creates=create_calls;
   assert(wr_iot_driver_close_retirement_prepare_fixed(&ad,&another)==-EBUSY);
   assert(!another&&create_calls==prior_creates&&handle->refs==2);
   assert(wr_iot_driver_close_retirement_reconcile(&ad,&handle)==-EAGAIN);
   assert(handle==&stopped_task&&handle->refs==2&&!task_locked);
   rtnl_held=0;
   assert(wr_iot_driver_close_retirement_reconcile(&ad,&handle)==-EBUSY);
   rtnl_held=1;
   /* Inject the pinned core mm_release completion, not a module flag. */
   stopped_task.vfork_done=NULL;
   unsigned long saved_generation=c->generation;reconcile_drift=1;
   assert(wr_iot_driver_close_retirement_reconcile(&ad,&handle)==-EUCLEAN);
   assert(c->retirement_handle==handle&&handle->refs==2);
   c->generation=saved_generation;
   assert(wr_iot_driver_close_progress(&ad,&dev,&progress)==-EAGAIN);
   handle=(struct task_struct *)c->retirement_handle;
   assert(!handle&&!c->retirement_handle&&stopped_task.refs==1&&c->module_held&&c->active);
   assert(wr_iot_driver_close_retirement_reconcile(&ad,&handle)==-EINVAL);
  }else{
   assert(!handle&&!c->retirement_task);
   assert(stop_calls==(scenario>=6));
   if(scenario>=6)assert(!stopped_task.refs&&!c->retirement_canceling);
  }
  assert(wr_iot_driver_close_blocks_adapter_retirement(c));
  continue;
 }
 assert(!launch_status);
 assert(wr_iot_driver_close_progress(&ad,&dev,&progress)==-EINPROGRESS&&create_calls==1);
 assert(!handle&&wake_calls==1&&stopped_task.refs==1&&c->retirement_task==&stopped_task);
 /* Inject core scheduling of the exact designated task after callback RTNL. */
 rtnl_held=0;test_current=&stopped_task;stopped_task.flags=PF_KTHREAD;
 if(scenario==1)ad.wr_iot_transition.retiring=1;
 if(scenario==2)stopped_task.flags|=PF_WQ_WORKER;
 if(!scenario)run_successful_body(&ad);
 else assert(wr_iot_driver_close_retirement_thread(&ad)==(scenario==1?-EBUSY:-EPERM));
 test_current=&creator_task;
 if(scenario){
  assert(!exit_calls&&chain_puts==1&&!body_rtnl&&!test_locked);
  assert(c->active&&c->module_held&&!c->retirement_module_transferred&&!c->retirement_task);
  assert(wr_iot_driver_close_blocks_adapter_retirement(c));
  continue;
 }
 assert(exit_calls==1&&chain_puts==1&&!body_rtnl&&!test_locked);
 assert(c->active&&c->retirement_module_transferred&&!c->module_held&&!c->retirement_task);
 assert(!wr_iot_driver_close_blocks_adapter_retirement(c));
 assert(c->synchronous_netdev_returned&&!c->recovery_netdev_transferred);
 rtnl_held=1;
 assert(!wr_iot_driver_close_progress(&ad,&dev,&progress)&&create_calls==1&&chain_puts==1);
 }
 puts("PASS composed synchronous chain: finish -> one dev_put receipt -> fixed create -> wake -> exact task claim -> core exit; active OPEN fence retained; scheduler/refs injected");
 return 0;
}
