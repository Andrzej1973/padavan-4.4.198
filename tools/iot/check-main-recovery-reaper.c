#include "main-open-recovery-owner.h"
#include "virtual-open-claim.h"
#include <assert.h>
#include <stddef.h>
#include <stdio.h>

#define WDEV_NUM_MAX 1
#define HZ 100
#define RT_DEBUG_ERROR 1
typedef void VOID;
typedef unsigned long ULONG;
typedef int INT;
struct work_struct { int pending; };
struct delayed_work { struct work_struct work; int pending; };
struct net_device { int held; void *priv; };
typedef struct adapter {
 int wr_iot_transition_lock;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX + 1];
 struct wr_iot_main_recovery_owner wr_iot_main_recovery;
 struct work_struct wr_iot_main_recovery_work;
 struct delayed_work wr_iot_main_recovery_reap_work;
 struct net_device *net_dev;
 int wr_iot_ticket_wait;
 unsigned int VirtualIfCnt;
} RTMP_ADAPTER,*PRTMP_ADAPTER;
static int locked,held_count,put_count,scheduled,joined,reaper_scheduled;
static int allow_schedule=1,allow_reaper=1;
#ifdef WR_IOT_EXTRACT_MAIN_OPEN
static int module_refs,close_begin_failure,preclose_failure;
#endif
#define container_of(ptr,type,member) ((type *)((char *)(ptr)-offsetof(type,member)))
#define to_delayed_work(work) container_of(work,struct delayed_work,work)
#define RTMP_IRQ_LOCK(lock,flags) ((void)(lock),(flags)=0,assert(!locked),locked=1)
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(lock),(void)(flags),assert(locked),locked=0)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define DBGPRINT(level,args) ((void)(level))
#define CONFIG_AP_SUPPORT 1
#define RT_MOD_INC_USE_COUNT() (++module_refs)
#define RT_MOD_DEC_USE_COUNT() (--module_refs)
#define GET_PAD_FROM_NET_DEV(ad,dev) ((ad)=(dev)->priv)
#define RTMP_DRIVER_AP_MAIN_OPEN(ad) ((void)(ad))
#define IS_MT7603(ad) ((void)(ad),1)
#define netif_start_queue(dev) ((void)(dev))
#define netif_carrier_on(dev) ((void)(dev))
#define netif_wake_queue(dev) ((void)(dev))
#define wake_up_all(wait) ((void)(wait))
static void dev_hold(struct net_device *dev){assert(dev);dev->held++;held_count++;}
static void dev_put(struct net_device *dev){assert(dev&&dev->held);dev->held--;put_count++;}
static int schedule_work(struct work_struct *work){
 assert(locked&&work);scheduled++;
 if(!allow_schedule)return 0;
 work->pending=1;return 1;
}
static int schedule_delayed_work(struct delayed_work *work,unsigned long delay){
 assert(locked&&work&&delay);reaper_scheduled++;
 if(!allow_reaper)return 0;
 work->pending=1;return 1;
}
static int cancel_work_sync(struct work_struct *work){
 int pending;
 assert(!locked&&work);joined++;pending=work->pending;work->pending=0;
 return pending;
}

#include "main-recovery-reaper.inc"

#ifdef WR_IOT_EXTRACT_MAIN_OPEN
static int mock_virtual_up(PRTMP_ADAPTER ad,struct net_device *dev,
 const struct wr_iot_radio_ticket *ticket,unsigned long generation){
 assert(ad&&dev&&ticket&&generation&&!locked);
 ad->VirtualIfCnt++;return 0;
}
#define VIRTUAL_IF_UP_CLAIM(ad,dev,ticket,generation) \
 mock_virtual_up((PRTMP_ADAPTER)(ad),(dev),(ticket),(generation))
static int wr_iot_main_readiness_verify(PRTMP_ADAPTER ad,
 struct net_device *dev,unsigned long generation){
 struct wr_iot_radio_ticket ticket;
 assert(ad&&dev&&generation&&!locked);
 assert(wr_iot_radio_begin(&ad->wr_iot_transition,
   ad->wr_iot_transition.epoch,WR_RADIO_VERIFY,&ticket));
 assert(wr_iot_radio_finish(&ad->wr_iot_transition,&ticket,0));
 return 0;
}
static int wr_iot_main_close_begin_checked(PRTMP_ADAPTER ad,
 struct net_device *dev,struct wr_iot_radio_ticket *ticket,
 unsigned long *generation,unsigned long *token,unsigned long *wait_serial){
 struct wr_iot_interface_ref *record;
 assert(ad&&dev&&ticket&&generation&&token&&wait_serial&&!locked);
 if(close_begin_failure)return -1;
 record=wr_iot_registry_find_owned(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev);
 assert(record);*generation=record->generation;*token=record->last_token;
 assert(wr_iot_main_stop_request(&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,dev,
   ad->VirtualIfCnt,ticket,wait_serial)==WR_MAIN_STOP_ADMITTED);
 assert(wr_iot_ref_begin_close(record,dev,*generation,*token));
 assert(wr_iot_main_close_claim_preclose(&ad->wr_iot_transition,record,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ticket,ad->VirtualIfCnt));
 return 0;
}
static int wr_iot_main_close_preclose_once(PRTMP_ADAPTER ad,
 struct net_device *dev,unsigned long generation,
 const struct wr_iot_radio_ticket *ticket){
 struct wr_iot_interface_ref *record=wr_iot_registry_find(
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,dev,generation);
 assert(record&&wr_iot_main_close_claim_void_preclose(record,ticket));
 if(preclose_failure)return -1;
 assert(wr_iot_main_close_finish_preclose(record,ticket));return 0;
}
static int wr_iot_main_close_continue_checked(PRTMP_ADAPTER ad,
 struct net_device *dev,unsigned long generation,unsigned long token,
 const struct wr_iot_radio_ticket *ticket){
 assert(ad&&dev&&generation&&token&&ticket);
 return -1; /* This fixture checks retained partial-close paths. */
}

/* ACTUAL_MAIN_OPEN */
static void test_extracted_main_open(void){
 int mode;
 for(mode=0;mode<3;mode++){
  RTMP_ADAPTER ad={0};struct net_device dev={0};
  struct wr_iot_interface_ref *record;unsigned long generation=0;
  ad.net_dev=&dev;dev.priv=&ad;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);
  wr_iot_main_recovery_init(&ad.wr_iot_main_recovery);
  record=wr_iot_registry_add_family(ad.wr_iot_interface_refs,
    WDEV_NUM_MAX+1,&generation,&dev,WR_REF_FAMILY_MAIN);
  assert(record);record->published=1;
  locked=held_count=put_count=scheduled=joined=reaper_scheduled=0;
  module_refs=0;allow_schedule=allow_reaper=1;
  close_begin_failure=(mode==0);preclose_failure=(mode==1);
  assert(MainVirtualIF_open(&dev)==-1);
  assert(!locked&&module_refs==1&&dev.held==1&&scheduled==1);
  assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_QUEUED);
  if(mode==0){
   assert(ad.wr_iot_main_recovery.source==WR_MAIN_RECOVERY_OPEN_ACQUIRED);
   assert(!ad.wr_iot_main_recovery.close_ticket_valid);
  }else{
   assert(ad.wr_iot_main_recovery.close_ticket_valid);
   assert(ad.wr_iot_main_recovery.source==
    (mode==1?WR_MAIN_RECOVERY_CLOSE_UNCERTAIN:
             WR_MAIN_RECOVERY_CLOSE_INCOMPLETE));
  }
 }
 puts("PASS extracted MainVirtualIF_open: three failed-VERIFY recovery paths");
}
#endif

static unsigned long setup(RTMP_ADAPTER *ad,struct net_device *dev){
 struct wr_iot_interface_ref *record;
 unsigned long generation=0;
 *ad=(RTMP_ADAPTER){0};*dev=(struct net_device){0};
 ad->net_dev=dev;ad->VirtualIfCnt=1;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.phase=WR_RADIO_UNVERIFIED;
 wr_iot_main_recovery_init(&ad->wr_iot_main_recovery);
 record=wr_iot_registry_add_family(ad->wr_iot_interface_refs,
                                   WDEV_NUM_MAX+1,&generation,dev,WR_REF_FAMILY_MAIN);
 assert(record);record->published=1;
 assert(wr_iot_ref_reserve(record,dev,generation,7));
 assert(wr_iot_ref_open_finish(record,dev,generation,7,1));
 locked=held_count=put_count=scheduled=joined=reaper_scheduled=0;
 allow_schedule=allow_reaper=1;
 return generation;
}
int main(void){
#ifdef WR_IOT_EXTRACT_MAIN_OPEN
 test_extracted_main_open();
#endif
 RTMP_ADAPTER ad;
 struct net_device dev;
 struct wr_iot_radio_ticket ticket;
 struct wr_iot_interface_ref *record;
 unsigned long generation=setup(&ad,&dev);
 assert(wr_iot_main_verify_recovery_submit(&ad,&dev,generation,NULL));
 assert(!locked&&dev.held==1&&held_count==1&&put_count==0);
 assert(scheduled==1&&reaper_scheduled==1&&
        ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_QUEUED&&
        ad.wr_iot_main_recovery.schedule_recorded);
 assert(wr_iot_main_recovery_rtnl_unavailable(&ad.wr_iot_main_recovery));
 assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_RETAINED);
 wr_iot_main_recovery_reap_work_fn(&ad.wr_iot_main_recovery_reap_work.work);
 assert(joined==1&&scheduled==2&&reaper_scheduled==2);
 assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_QUEUED&&dev.held==1);
 ad.wr_iot_main_recovery.phase=WR_MAIN_OWNER_RUNNING;
 ad.wr_iot_main_recovery.completed=1;
 ad.wr_iot_main_recovery.module_pin_released=1;
 wr_iot_main_recovery_reap_work_fn(&ad.wr_iot_main_recovery_reap_work.work);
 assert(joined==2&&dev.held==0&&put_count==1);
 assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_IDLE&&
        !ad.wr_iot_main_recovery.deferred_owners);

 generation=setup(&ad,&dev);
 assert(wr_iot_main_verify_recovery_submit(&ad,&dev,generation,NULL));
 /* Reaper fires before main callback: cancel reports pending work. */
 wr_iot_main_recovery_reap_work_fn(&ad.wr_iot_main_recovery_reap_work.work);
 assert(joined==1&&scheduled==2&&
        ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_QUEUED&&
        ad.wr_iot_main_recovery.attempts==0&&dev.held==1);

 generation=setup(&ad,&dev);allow_schedule=0;
 assert(wr_iot_main_verify_recovery_submit(&ad,&dev,generation,NULL));
 assert(ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_RETAINED&&
        ad.wr_iot_main_recovery.failed_submissions==1&&dev.held==1);
 wr_iot_main_recovery_reap_work_fn(&ad.wr_iot_main_recovery_reap_work.work);
 assert(joined==1&&ad.wr_iot_main_recovery.phase==WR_MAIN_OWNER_RETAINED&&
        dev.held==1);
 generation=setup(&ad,&dev);ad.wr_iot_transition.retiring=1;
 assert(!wr_iot_main_verify_recovery_submit(&ad,&dev,generation,NULL));
 assert(dev.held==0&&held_count==1&&put_count==1&&scheduled==0);
 generation=setup(&ad,&dev);
 record=wr_iot_registry_find_owned(ad.wr_iot_interface_refs,
                                   WDEV_NUM_MAX+1,&dev);
 assert(record&&wr_iot_radio_begin_main_stop(&ad.wr_iot_transition,1,&ticket));
 assert(wr_iot_ref_begin_close(record,&dev,generation,record->last_token));
 assert(wr_iot_main_close_claim_preclose(&ad.wr_iot_transition,record,
        ad.wr_iot_interface_refs,WDEV_NUM_MAX+1,&ticket,1));
 assert(wr_iot_main_close_claim_void_preclose(record,&ticket));
 assert(wr_iot_main_close_finish_preclose(record,&ticket));
 assert(wr_iot_main_verify_recovery_submit(&ad,&dev,generation,&ticket));
 assert(ad.wr_iot_main_recovery.source==WR_MAIN_RECOVERY_CLOSE_INCOMPLETE&&
        ad.wr_iot_main_recovery.close_ticket_valid&&dev.held==1);
 puts("PASS main recovery reaper host model: queue, joined retry, exact dev hold/release, rejected schedule, retirement fence");
 return 0;
}
