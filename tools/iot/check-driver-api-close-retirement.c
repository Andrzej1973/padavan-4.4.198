#if defined(WR_CLOSE_THREAD_BODY_TEST) && !defined(WR_CLOSE_START_BINDING_TEST)
#define WR_CLOSE_START_BINDING_TEST
#endif
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "driver-api-close-retirement.h"
#ifdef WR_CLOSE_KERNEL_BINDING_TEST
#define INT int
typedef unsigned long ULONG;
#define WDEV_NUM_MAX 1
struct work_struct {int busy;};
typedef struct {
 int chip,wr_iot_transition_lock;unsigned count;
 void *net_dev;
 struct {unsigned BssidNum;struct {struct {const void *if_dev;}wdev;}MBSSID[3];}ApCfg;
 struct wr_iot_driver_close_owner wr_iot_close_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[2];
 struct wr_iot_mbss_poll_lifetime wr_iot_mbss_poll_state;
 struct wr_iot_mbss_reaper_gate wr_iot_mbss_reaper_gate;
 struct {unsigned deferred_owners;}wr_iot_main_recovery;
 struct work_struct wr_iot_main_recovery_work;
 struct {struct work_struct work;}wr_iot_main_recovery_reap_work,wr_iot_mbss_poll_work,wr_iot_mbss_work[2];
} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->chip)
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
static int test_locked;
#ifdef WR_CLOSE_LAUNCH_TEST
static RTMP_ADAPTER *launch_ad;static int launch_drift;
#endif
static int work_busy(struct work_struct *w){
 assert(test_locked);
#ifdef WR_CLOSE_LAUNCH_TEST
 if(launch_ad&&launch_drift&&launch_ad->wr_iot_close_owner.retirement_task){
  launch_ad->wr_iot_transition.retiring=1;launch_drift=0;
 }
#endif
 return w->busy;
}
#include "driver-api-close-retirement-binding.inc"
#ifdef WR_CLOSE_CREATE_BINDING_TEST
#include <errno.h>
struct task_struct {unsigned refs,flags;void *vfork_done;};
static struct task_struct stopped_task,creator_task;
#ifdef WR_CLOSE_DYNAMIC_CURRENT_TEST
static struct task_struct *test_current=&creator_task;
#define current test_current
#else
#define current (&creator_task)
#endif
static RTMP_ADAPTER *create_ad;
static int stop_result=-EINTR,stop_drift;
static int create_mode,create_calls,stop_calls,body_calls;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!test_locked);test_locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(test_locked);test_locked=0;}while(0)
#define IS_ERR(p) ((p)==(void *)-12L)
#define PTR_ERR(p) ((int)(long)(p))
#ifdef WR_CLOSE_THREAD_BODY_TEST
static int wr_iot_driver_close_retirement_thread(void *context);
#endif
static int retirement_body(void *ad){(void)ad;body_calls++;return 0;}
static struct task_struct *kthread_create(int (*fn)(void *),void *data,const char *name){
 assert(!test_locked&&name);
#ifdef WR_CLOSE_THREAD_BODY_TEST
 assert(fn==retirement_body||fn==wr_iot_driver_close_retirement_thread);
#else
 assert(fn==retirement_body);
#endif
create_calls++;create_ad=data;
 if(create_mode==1)return (void *)-12L;
 if(create_mode==2)((RTMP_ADAPTER *)data)->wr_iot_transition.retiring=1;
 if(create_mode==3)return 0;
 stopped_task.refs=1;stopped_task.vfork_done=&stopped_task;return &stopped_task;
}
static void get_task_struct(struct task_struct *t){assert(!test_locked);t->refs++;}
static void put_task_struct(struct task_struct *t){assert(!test_locked&&t->refs);t->refs--;}
static int kthread_stop(struct task_struct *t){assert(!test_locked&&t==&stopped_task&&t->refs);stop_calls++;t->refs--;if(stop_drift)create_ad->wr_iot_close_owner.generation++;return stop_result;}
static int rtnl_held=1;
static int rtnl_is_locked(void){return rtnl_held;}
#include "driver-api-close-retirement-create.inc"
#include "driver-api-close-retirement-cancel.inc"
#ifdef WR_CLOSE_THREAD_ENTRY_TEST
#define PF_KTHREAD 1U
#define PF_WQ_WORKER 2U
#include "driver-api-close-retirement-thread-entry.inc"
#endif
#ifdef WR_CLOSE_THREAD_BODY_TEST
#include <setjmp.h>
static jmp_buf exit_jump;
static int body_rtnl,exit_calls;
static void rtnl_lock(void){assert(!body_rtnl&&!test_locked);body_rtnl=1;}
static void rtnl_unlock(void){assert(body_rtnl&&!test_locked);body_rtnl=0;}
static void module_put_and_exit(int status) __attribute__((noreturn));
static void module_put_and_exit(int status){assert(!status&&!body_rtnl&&!test_locked);exit_calls++;longjmp(exit_jump,1);}
#include "driver-api-close-retirement-thread-body.inc"
static void run_successful_body(RTMP_ADAPTER *ad){
 if(!setjmp(exit_jump)){
  wr_iot_driver_close_retirement_thread(ad);
  assert(!"successful body returned instead of nonreturning core tail");
 }
}
#endif
#ifdef WR_CLOSE_START_BINDING_TEST
static int wake_calls,wake_accept=1;
static int wake_up_process(struct task_struct *t){assert(test_locked&&t==&stopped_task);wake_calls++;return wake_accept;}
#include "driver-api-close-retirement-start.inc"
#endif
#endif
#endif
int main(void){
 #ifdef WR_CLOSE_KERNEL_BINDING_TEST
 const unsigned cases=20;
#else
 const unsigned cases=17;
#endif
 for(unsigned fault=0;fault<cases;fault++){
  struct wr_iot_driver_close_owner close={0};struct wr_iot_radio_transition radio;
  struct wr_iot_interface_ref refs[2]={{0}};struct wr_iot_mbss_recovery_owner owners[2];
  struct wr_iot_mbss_poll_lifetime poll;struct wr_iot_mbss_reaper_gate reaper;
  int main_dev,dev,idle=1;unsigned long seq=0;
  wr_iot_radio_transition_init(&radio);radio.phase=WR_RADIO_READY;radio.main_ready=1;
  wr_iot_mbss_poll_init(&poll);wr_iot_mbss_reaper_gate_init(&reaper);
  for(unsigned i=0;i<2;i++)wr_iot_mbss_recovery_init(&owners[i]);
  struct wr_iot_interface_ref *main=wr_iot_registry_add_family(refs,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(refs,2,&seq,&dev,WR_REF_FAMILY_MBSS);
  main->published=r->published=1;main->phase=WR_REF_OWNED;main->last_token=1;r->last_token=2;
  close.active=close.consumed=close.module_held=close.recovery_netdev_transferred=close.recovery_netdev_returned=1;
  close.device=&dev;close.generation=2;close.open_token=2;close.ticket.epoch=radio.epoch;
  close.ticket.serial=3;close.ticket.operation=WR_RADIO_BSS_CLOSE;
  r->phase=WR_REF_IDLE;r->close_stage=4;r->close_serial=3;r->close_epoch=radio.epoch;r->close_vendor_count=2;
  switch(fault){case 1:poll.unjoined=1;break;case 2:poll.pending=1;break;case 3:poll.running=1;break;
   case 4:poll.joining=1;break;case 5:reaper.reaping=1;break;case 6:owners[1].deferred_owners=1;break;
   case 7:idle=0;break;case 8:close.recovery_netdev_returned=0;break;case 9:close.recovery_join_pending=1;break;
   case 10:r->generation++;break;case 11:main->close_running=1;break;case 12:radio.retiring=1;break;
   case 13:close.module_held=0;break;case 14:close.netdev_held=1;break;case 15:close.ticket.epoch++;break;
   case 16:r->close_prior_ready++;break;
   case 17:idle=2;break;case 18:idle=3;break;case 19:idle=4;break;}
  struct wr_iot_driver_close_owner before=close;
#ifdef WR_CLOSE_KERNEL_BINDING_TEST
  static RTMP_ADAPTER ad;memset(&ad,0,sizeof(ad));ad.chip=1;ad.count=1;ad.net_dev=&main_dev;
  ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=close.device;
  ad.wr_iot_close_owner=close;ad.wr_iot_transition=radio;
  memcpy(ad.wr_iot_interface_refs,refs,sizeof(refs));memcpy(ad.wr_iot_mbss_recovery,owners,sizeof(owners));
  ad.wr_iot_mbss_poll_state=poll;ad.wr_iot_mbss_reaper_gate=reaper;
  if(idle==0)ad.wr_iot_mbss_work[1].work.busy=1;
  if(idle==2)ad.wr_iot_main_recovery_work.busy=1;
  if(idle==3)ad.wr_iot_main_recovery_reap_work.work.busy=1;
  if(idle==4)ad.wr_iot_mbss_poll_work.work.busy=1;
#ifdef WR_CLOSE_CREATE_BINDING_TEST
  if(fault){
   struct task_struct *task=(void *)1;create_calls=0;
   assert(wr_iot_driver_close_retirement_prepare(&ad,retirement_body,&task)==-EBUSY);
   assert(!task&&!create_calls);
  }
  if(!fault){
   for(create_mode=0;create_mode<4;create_mode++){
    ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
    create_calls=stop_calls=body_calls=0;
    struct task_struct *task=(void *)1;
    int status=wr_iot_driver_close_retirement_prepare(&ad,retirement_body,&task);
    assert(status==(create_mode==0?0:create_mode==1?-ENOMEM:create_mode==2?-EBUSY:-EUCLEAN));
    assert(create_calls==1&&!body_calls&&!test_locked&&ad.wr_iot_close_owner.module_held);
    if(!create_mode){
     assert(task==&stopped_task&&task->refs==2&&ad.wr_iot_close_owner.retirement_task==task);
     struct task_struct *self=current;
     assert(wr_iot_driver_close_retirement_cancel(&ad,&self)==-EDEADLK&&!stop_calls);
     struct task_struct other={.refs=1},*foreign=&other;
     assert(wr_iot_driver_close_retirement_cancel(&ad,&foreign)==-EBUSY&&!stop_calls);
     ad.wr_iot_close_owner.retirement_started=1;
     assert(wr_iot_driver_close_retirement_cancel(&ad,&task)==-EBUSY&&!stop_calls);
     ad.wr_iot_close_owner.retirement_started=0;
     rtnl_held=0;
     assert(wr_iot_driver_close_retirement_cancel(&ad,&task)==-EBUSY&&!stop_calls);
     rtnl_held=1;
     assert(!wr_iot_driver_close_retirement_cancel(&ad,&task));
     assert(!task&&!stopped_task.refs&&stop_calls==1&&!ad.wr_iot_close_owner.retirement_task);
     assert(ad.wr_iot_close_owner.module_held&&ad.wr_iot_close_owner.active&&!body_calls);
     assert(wr_iot_driver_close_retirement_cancel(&ad,&task)==-EINVAL&&stop_calls==1);
     for(unsigned cancel_fault=0;cancel_fault<2;cancel_fault++){
      ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
      assert(!wr_iot_driver_close_retirement_prepare(&ad,retirement_body,&task));
      stop_result=cancel_fault?-EINTR:0;stop_drift=cancel_fault;
      assert(wr_iot_driver_close_retirement_cancel(&ad,&task)==-EUCLEAN);
      assert(task==&stopped_task&&task->refs==1&&ad.wr_iot_close_owner.retirement_canceling);
      assert(ad.wr_iot_close_owner.retirement_task==task&&ad.wr_iot_close_owner.module_held);
      stop_result=-EINTR;stop_drift=0;
     }
    }
    else{assert(!task&&!ad.wr_iot_close_owner.retirement_task);assert(stop_calls==(create_mode==2));if(create_mode==2)assert(!stopped_task.refs);}
   }
   ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
#ifdef WR_CLOSE_THREAD_ENTRY_TEST
   for(unsigned entry_fault=0;entry_fault<6;entry_fault++){
    ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
    ad.wr_iot_close_owner.retirement_task=current;ad.wr_iot_close_owner.retirement_started=1;
    creator_task.flags=PF_KTHREAD;
    if(entry_fault==1)creator_task.flags=0;
    if(entry_fault==2)creator_task.flags|=PF_WQ_WORKER;
    if(entry_fault==3)ad.wr_iot_close_owner.retirement_task=&stopped_task;
    if(entry_fault==4)ad.wr_iot_transition.retiring=1;
    if(entry_fault==5)ad.wr_iot_close_owner.retirement_canceling=1;
    struct wr_iot_driver_close_owner entering=ad.wr_iot_close_owner;
    int status=wr_iot_driver_close_retirement_thread_enter(&ad);
    assert(status==(entry_fault==0?0:entry_fault<3?-EPERM:-EBUSY));
    assert(ad.wr_iot_close_owner.module_held&&ad.wr_iot_close_owner.active&&!test_locked);
    if(!entry_fault){assert(ad.wr_iot_close_owner.retirement_entered);assert(wr_iot_driver_close_retirement_thread_enter(&ad)==-EBUSY);}
    else assert(!memcmp(&entering,&ad.wr_iot_close_owner,sizeof(entering)));
    assert(!wr_iot_driver_close_retirement_thread_refuse(&ad,0));
    struct wr_iot_driver_close_owner refusing=ad.wr_iot_close_owner;
    assert(wr_iot_driver_close_retirement_thread_refuse(&ad,-EAGAIN)==(entry_fault!=3));
    assert(ad.wr_iot_close_owner.module_held&&ad.wr_iot_close_owner.active);
    if(entry_fault!=3){
     assert(!ad.wr_iot_close_owner.retirement_task&&!ad.wr_iot_close_owner.retirement_started&&!ad.wr_iot_close_owner.retirement_entered);
     assert(ad.wr_iot_close_owner.retirement_error==-EAGAIN);
     assert(ad.wr_iot_close_owner.retirement_canceling==(entry_fault==5));
     refusing=ad.wr_iot_close_owner;
    }
    assert(!wr_iot_driver_close_retirement_thread_refuse(&ad,-EAGAIN));
    assert(!memcmp(&refusing,&ad.wr_iot_close_owner,sizeof(refusing)));
   }
   ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
   creator_task.flags=PF_KTHREAD;
   assert(!wr_iot_driver_close_retirement_thread_claim(&ad));
   ad.wr_iot_close_owner.retirement_task=current;
   ad.wr_iot_close_owner.retirement_started=1;
   assert(!wr_iot_driver_close_retirement_thread_enter(&ad));
   ad.wr_iot_close_owner.retirement_canceling=1;
   struct wr_iot_driver_close_owner denied=ad.wr_iot_close_owner;
   assert(!wr_iot_driver_close_retirement_thread_claim(&ad));
   assert(!memcmp(&denied,&ad.wr_iot_close_owner,sizeof(denied)));
   ad.wr_iot_close_owner.retirement_canceling=0;
   ad.wr_iot_transition.epoch++;
   denied=ad.wr_iot_close_owner;
   assert(!wr_iot_driver_close_retirement_thread_claim(&ad));
   assert(!memcmp(&denied,&ad.wr_iot_close_owner,sizeof(denied)));
   ad.wr_iot_transition=radio;
   assert(wr_iot_driver_close_retirement_thread_claim(&ad));
   assert(ad.wr_iot_close_owner.active&&!ad.wr_iot_close_owner.module_held&&
    ad.wr_iot_close_owner.retirement_module_transferred&&!ad.wr_iot_close_owner.retirement_task);
   assert(!wr_iot_driver_close_retirement_thread_claim(&ad));
#ifdef WR_CLOSE_THREAD_BODY_TEST
   ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
   create_mode=0;struct task_struct *fixed_task=0;
   assert(!wr_iot_driver_close_retirement_prepare_fixed(&ad,&fixed_task));
   assert(fixed_task==&stopped_task);
   wake_calls=0;wake_accept=rtnl_held=1;
   assert(!wr_iot_driver_close_retirement_start(&ad,&fixed_task));
   assert(!fixed_task&&!ad.wr_iot_close_owner.retirement_handle);
   /* No actual scheduler: execute exact fixed body as designated current. */
   ad.wr_iot_close_owner.retirement_task=current;
   ad.wr_iot_close_owner.retirement_started=1;
   exit_calls=0;
   run_successful_body(&ad);
   assert(exit_calls==1&&!body_rtnl&&ad.wr_iot_close_owner.active&&
    !ad.wr_iot_close_owner.module_held&&ad.wr_iot_close_owner.retirement_module_transferred);
   ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
   ad.wr_iot_close_owner.retirement_task=current;
   ad.wr_iot_close_owner.retirement_started=1;
   ad.wr_iot_transition.retiring=1;
   assert(wr_iot_driver_close_retirement_thread(&ad)==-EBUSY);
   assert(exit_calls==1&&!body_rtnl&&ad.wr_iot_close_owner.module_held&&
    !ad.wr_iot_close_owner.retirement_task&&ad.wr_iot_close_owner.active);
   ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
   ad.wr_iot_close_owner.retirement_task=current;
   ad.wr_iot_close_owner.retirement_started=1;
   creator_task.flags=PF_KTHREAD|PF_WQ_WORKER;
   assert(wr_iot_driver_close_retirement_thread(&ad)==-EPERM);
   assert(exit_calls==1&&!body_rtnl&&ad.wr_iot_close_owner.module_held&&
    !ad.wr_iot_close_owner.retirement_task&&ad.wr_iot_close_owner.active);
#endif
   ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;creator_task.flags=0;
#endif
#ifdef WR_CLOSE_START_BINDING_TEST
   create_mode=0;
   for(unsigned start_fault=0;start_fault<5;start_fault++){
    ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
    wake_calls=0;wake_accept=start_fault!=1;rtnl_held=1;
    struct task_struct *task=0;
    assert(!wr_iot_driver_close_retirement_prepare(&ad,retirement_body,&task));
    struct task_struct *self=current,other={.refs=1},*foreign=&other;
    assert(wr_iot_driver_close_retirement_start(&ad,&self)==-EDEADLK&&!wake_calls);
    assert(wr_iot_driver_close_retirement_start(&ad,&foreign)==-EBUSY&&!wake_calls);
    if(start_fault==2)ad.wr_iot_transition.retiring=1;
    if(start_fault==3)ad.wr_iot_close_owner.retirement_canceling=1;
    if(start_fault==4)rtnl_held=0;
    int status=wr_iot_driver_close_retirement_start(&ad,&task);
    assert(status==(start_fault==0?0:start_fault==1?-EUCLEAN:-EBUSY));
    assert(!body_calls&&ad.wr_iot_close_owner.module_held&&ad.wr_iot_close_owner.active);
    if(!start_fault){
     assert(!task&&wake_calls==1&&stopped_task.refs==1&&ad.wr_iot_close_owner.retirement_started);
     assert(wr_iot_driver_close_retirement_start(&ad,&task)==-EINVAL&&wake_calls==1);
    }else if(start_fault==1){
     assert(task==&stopped_task&&wake_calls==1&&task->refs==2&&ad.wr_iot_close_owner.retirement_started);
     assert(wr_iot_driver_close_retirement_cancel(&ad,&task)==-EBUSY);
     assert(wr_iot_driver_close_retirement_start(&ad,&task)==-EBUSY&&wake_calls==1);
    }else assert(task==&stopped_task&&!wake_calls&&task->refs==2&&!ad.wr_iot_close_owner.retirement_started);
   }
   ad.wr_iot_close_owner=before;ad.wr_iot_transition=radio;
#endif
  }
#endif
  test_locked=1;
  assert(wr_iot_driver_close_retirement_ready_locked(&ad)==(fault==0));
  assert(!wr_iot_driver_close_retirement_designate_locked(&ad,0));
  assert(wr_iot_driver_close_retirement_designate_locked(&ad,&dev)==(fault==0));
  if(!fault){
   assert(ad.wr_iot_close_owner.retirement_task==&dev&&ad.wr_iot_close_owner.module_held&&ad.wr_iot_close_owner.active);
   struct wr_iot_driver_close_owner designated=ad.wr_iot_close_owner;
   assert(!wr_iot_driver_close_retirement_designate_locked(&ad,&main_dev));
   assert(!memcmp(&designated,&ad.wr_iot_close_owner,sizeof(designated)));
  }else assert(!memcmp(&before,&ad.wr_iot_close_owner,sizeof(before)));
  test_locked=0;
#else
  assert(wr_iot_driver_close_retirement_ready(&close,&radio,refs,2,&main_dev,1,owners,2,&poll,&reaper,idle)==(fault==0));
#endif
  if(!fault){
   close.recovery_netdev_transferred=close.recovery_netdev_returned=0;
   close.reference_completed=close.synchronous_netdev_returned=1;
   assert(wr_iot_driver_close_retirement_ready(&close,&radio,refs,2,&main_dev,1,owners,2,&poll,&reaper,1));
   close.synchronous_put_pending=1;
   assert(!wr_iot_driver_close_retirement_ready(&close,&radio,refs,2,&main_dev,1,owners,2,&poll,&reaper,1));
   close.synchronous_put_pending=0;
   close.recovery_netdev_transferred=close.recovery_netdev_returned=1;
   assert(!wr_iot_driver_close_retirement_ready(&close,&radio,refs,2,&main_dev,1,owners,2,&poll,&reaper,1));
   close=before;
  }
  assert(!memcmp(&before,&close,sizeof(close)));
 }
 puts("PASS retirement preflight: exact returned receipt, durable close/Main and joined poll/recovery/work;conflicts refuse without ownership mutation; thread/release unbound");
 return 0;
}
