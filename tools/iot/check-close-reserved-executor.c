#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include "driver-api-close-recovery.h"
#include "mbss-recovery-storage.h"
#define MBSS_SUPPORT 1
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define WDEV_NUM_MAX 1
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
#define CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE 1
typedef int INT;typedef int BOOLEAN;typedef unsigned int UINT;typedef unsigned int UINT32;typedef unsigned long ULONG;typedef void VOID;
typedef struct adapter RTMP_ADAPTER,*PRTMP_ADAPTER;
struct device {RTMP_ADAPTER *ad;};typedef struct device *PNET_DEV;
struct work_struct {int busy;};
struct wr_iot_mbss_work_context {struct work_struct work;RTMP_ADAPTER *adapter;unsigned slot;};
struct adapter {
 PNET_DEV net_dev;int wr_iot_transition_lock,wr_iot_ticket_wait;unsigned count;
 struct {unsigned char BssidNum;}ApCfg;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_mbss_recovery_owner wr_iot_mbss_recovery[2];
 struct wr_iot_mbss_work_context wr_iot_mbss_work[2];
};
static int held,fail,cr_calls,vendor_calls,down_calls,module_refs;
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define VIRTUAL_IF_NUM(ad) ((ad)->count)
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);(flags)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);(void)(flags);assert(held);held=0;}while(0)
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
static unsigned work_busy(struct work_struct *w){assert(held);return w->busy;}
static int wr_iot_os_join_context(void){return 0;}
static int cr_disable(RTMP_ADAPTER *ad){assert(!held);cr_calls++;if(fail==5)ad->wr_iot_interface_refs[1].generation++;return fail==1?-1:0;}
#define RTMP_AP_IoctlHandle(a,b,c,d,e,f) ((void)(a),(void)(b),(void)(c),(void)(d),(void)(e),(void)(f),cr_disable(a))
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) do{assert(dev&&!held);}while(0)
static int MBSS_Close(PNET_DEV dev){assert(dev&&!held);vendor_calls++;if(fail==6)dev->ad->wr_iot_interface_refs[1].generation++;return fail==2?-1:0;}
static int RT28xx_MBSS_IdxGet(RTMP_ADAPTER *ad,PNET_DEV dev){assert(ad&&dev&&!held);return 2;}
#define MAX_MBSSID_NUM(ad) ((ad)->ApCfg.BssidNum)
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *ad,UINT32 id){assert(ad&&id==2&&!held);return fail==3?1:0;}
static int WrBeaconTxSOutstanding(RTMP_ADAPTER *ad,UINT32 id){assert(ad&&id==2&&!held);return fail==4?-1:0;}
static int wr_iot_virtual_down_checked(RTMP_ADAPTER *ad,const struct wr_iot_radio_ticket *ticket){assert(ad&&ticket&&!held&&ad->count==2);down_calls++;ad->count--;return 0;}
#define wake_up_all(wait) do{(void)(wait);assert(!held);}while(0)
#define RT_MOD_DEC_USE_COUNT() do{assert(!held&&module_refs==2);module_refs--;}while(0)
#include "mbss-close-checked.inc"
#include "mbss-recovery-work.inc"
int main(void){
 for(fail=0;fail<7;fail++){
  RTMP_ADAPTER ad={0};struct device main={&ad},dev={&ad};unsigned long seq=0;
  struct wr_iot_driver_close_owner close={0};
  held=cr_calls=vendor_calls=down_calls=0;module_refs=2;
  ad.net_dev=&main;ad.count=2;ad.ApCfg.BssidNum=3;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  struct wr_iot_interface_ref *m=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&seq,&main,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&seq,&dev,WR_REF_FAMILY_MBSS);
  m->published=r->published=1;m->phase=r->phase=WR_REF_OWNED;m->last_token=1;r->last_token=2;
  assert(wr_iot_radio_begin_stop(&ad.wr_iot_transition,2,&close.ticket));unsigned long serial=close.ticket.serial;
  close.active=close.uncertain=close.netdev_held=close.module_held=1;close.device=&dev;close.generation=2;close.open_token=2;
  r->close_epoch=close.ticket.epoch;r->close_vendor_count=2;r->close_prior_phase=(int)close.ticket.prior_phase;r->close_prior_ready=close.ticket.prior_ready;
  struct wr_iot_mbss_recovery_owner *owner=&ad.wr_iot_mbss_recovery[1];wr_iot_mbss_recovery_init(owner);
  ad.wr_iot_mbss_work[1].adapter=&ad;ad.wr_iot_mbss_work[1].slot=1;
  assert(wr_iot_driver_close_transfer_recovery(&close,owner,r,&ad.wr_iot_transition));
  wr_iot_mbss_recovery_work_fn(&ad.wr_iot_mbss_work[1].work);
  assert(!held&&ad.wr_iot_transition.serial==serial&&cr_calls==1);
  assert(close.active&&close.module_held&&close.recovery_netdev_transferred);
  if(fail==0){assert(owner->completed&&r->close_stage==4&&module_refs==1&&down_calls==1&&vendor_calls==1);}
  else{
   assert(!owner->completed&&owner->phase==WR_MBSS_OWNER_RETAINED&&module_refs==2&&!down_calls);
   if(fail==3){
    assert(r->close_stage==2&&owner->source==WR_MBSS_RECOVERY_RESERVED_CLOSE);
    int saved=fail;fail=0;assert(wr_iot_mbss_recovery_requeue(owner,3));
    wr_iot_mbss_recovery_work_fn(&ad.wr_iot_mbss_work[1].work);fail=saved;
    assert(owner->completed&&module_refs==1&&cr_calls==1&&vendor_calls==1&&down_calls==1);
   }else{
    if(fail<5)assert(r->close_stage==5&&owner->source==WR_MBSS_RECOVERY_UNCERTAIN);
    else{
     /* Drift after a successful raw call leaves no proof of the next stage.
      * Do not retry that call or clear the new registration's running flag. */
     assert(r->close_stage==(unsigned)(fail==5?0:1));
     assert(r->generation!=owner->generation&&r->close_running);
    }
    unsigned calls=(unsigned)(cr_calls+vendor_calls);
    assert(wr_iot_mbss_recovery_requeue(owner,3));wr_iot_mbss_recovery_work_fn(&ad.wr_iot_mbss_work[1].work);
    assert((unsigned)(cr_calls+vendor_calls)==calls&&!owner->completed&&module_refs==2);
   }
  }
 }
 puts("PASS actual worker + checked MBSS executor: reserved ticket retained, success consumes original module only, DMA retry skips vendor repeat, uncertain failures retain; hardware stubs only");
 return 0;
}
