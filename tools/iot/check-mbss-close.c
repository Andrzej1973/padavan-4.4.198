#include <radio-transition.h>
#include <interface-registry.h>
#include <assert.h>
#include <stddef.h>
#include <string.h>
typedef int INT;typedef unsigned long ULONG;
typedef unsigned int UINT32;
#define WDEV_NUM_MAX 1
#define NDIS_STATUS_SUCCESS 0
#define CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE 1
struct device;
typedef struct adapter {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;struct wr_iot_interface_ref wr_iot_interface_refs[2];struct device *net_dev;unsigned int VirtualIfCnt;struct {int BssidNum;} ApCfg;} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;
static int held,refs,cr_result,close_result,down_result,cr_calls,close_calls,queue_stops,hnat_calls,down_calls,reuse_on_close,invalidate_epoch_on_down,invalidate_token_on_down,inflate_count_on_down;
#ifdef MT_MAC
static int txs_outstanding;
#ifdef RTMP_PCI_SUPPORT
static int dma_outstanding;
#endif
#define MAX_MBSSID_NUM(ad) (2)
static int RT28xx_MBSS_IdxGet(PRTMP_ADAPTER ad,PNET_DEV dev){assert(ad&&dev&&!held);return 1;}
static int WrBeaconTxSOutstanding(PRTMP_ADAPTER ad,UINT32 bss){assert(ad&&bss==1&&!held);return txs_outstanding;}
#ifdef RTMP_PCI_SUPPORT
static int WrBeaconDmaOutstanding(PRTMP_ADAPTER ad,UINT32 bss){assert(ad&&bss==1&&!held);return dma_outstanding;}
#endif
#endif
#define RTMP_IRQ_LOCK(lock,flags) ((flags)=0,(void)(lock),assert(!held),held=1)
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(flags),(void)(lock),assert(held),held=0)
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) ((void)(dev),assert(!held),queue_stops++)
#define RT_MOD_HNAT_DEREG(dev) ((void)(dev),assert(!held),hnat_calls++)
#define RT_MOD_DEC_USE_COUNT() (--refs)
#ifdef MT_MAC
static int RTMP_AP_IoctlHandle(void *ad,void *unused,int cmd,int z,PNET_DEV dev,int n){assert(ad==dev->ad&&!unused&&cmd==1&&!z&&!n&&!held);cr_calls++;return cr_result;}
#endif
static int MBSS_Close(PNET_DEV dev){
 assert(dev&&!held);close_calls++;
 if(reuse_on_close){
  struct wr_iot_interface_ref *r=&dev->ad->wr_iot_interface_refs[0];
  wr_iot_ref_init(r,dev,2);r->published=1;
 }
 return close_result;
}
static int wr_iot_virtual_down_checked(PRTMP_ADAPTER ad,const struct wr_iot_radio_ticket *t){assert(ad&&t&&!held);down_calls++;if(invalidate_epoch_on_down)ad->wr_iot_transition.epoch=0;if(invalidate_token_on_down)ad->wr_iot_interface_refs[0].last_token=2;if(!down_result&&ad->wr_iot_transition.virtual_down_stage!=2){assert(ad->VirtualIfCnt>1);ad->VirtualIfCnt--;ad->wr_iot_transition.virtual_down_stage=2;}if(inflate_count_on_down)ad->VirtualIfCnt++;return down_result;}
#ifdef WR_IOT_V40
#include "wr-iot-mbss-close-checked.inc"
#else
#include "mbss-close-checked.inc"
#endif
static void set_main_owner(struct adapter *ad,struct device *main_dev){
 struct wr_iot_interface_ref *r=&ad->wr_iot_interface_refs[1];
 wr_iot_ref_init(r,main_dev,1);r->family=WR_REF_FAMILY_MAIN;
 r->published=1;assert(wr_iot_ref_reserve(r,main_dev,1,1));
 assert(wr_iot_ref_open_finish(r,main_dev,1,1,1));
}
int main(void){
 struct adapter a;struct device main_dev={&a},dev={&a};struct wr_iot_radio_ticket t,bad;
 unsigned long generation;
 for(int mode=0;mode<3;mode++){
  memset(&a,0,sizeof(a));a.net_dev=&main_dev;a.VirtualIfCnt=2;a.ApCfg.BssidNum=2;wr_iot_radio_transition_init(&a.wr_iot_transition);a.wr_iot_transition.phase=WR_RADIO_UNVERIFIED;a.wr_iot_transition.serial=1;
  struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];wr_iot_ref_init(r,&dev,1);r->family=WR_REF_FAMILY_MBSS;r->published=1;assert(wr_iot_ref_reserve(r,&dev,1,1));assert(wr_iot_ref_open_finish(r,&dev,1,1,1));
  assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==-1&&!generation&&!a.wr_iot_transition.busy);
  set_main_owner(&a,&main_dev);
  assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==0&&generation==1);
  refs=1;cr_calls=close_calls=queue_stops=hnat_calls=down_calls=held=reuse_on_close=0;cr_result=close_result=0;down_result=1;
  if(mode==1)close_result=1;
  if(mode==2)cr_result=1;
  assert(wr_iot_mbss_close_checked(&dev,0,&t)==-1&&!close_calls&&!down_calls);
  assert(wr_iot_mbss_close_checked(&dev,2,&t)==-1&&!close_calls&&!down_calls);
#ifdef WR_IOT_V40
  bad=t;bad.epoch++;
  assert(wr_iot_mbss_close_checked(&dev,1,&bad)==-1&&
         !queue_stops&&!close_calls&&!down_calls);
  bad=t;bad.prior_ready=!t.prior_ready;
  assert(wr_iot_mbss_close_checked(&dev,1,&bad)==-1&&
         !queue_stops&&!close_calls&&!down_calls);
  bad=t;bad.prior_phase=WR_RADIO_DOWN;
  assert(wr_iot_mbss_close_checked(&dev,1,&bad)==-1&&
         !queue_stops&&!close_calls&&!down_calls);
  bad=t;bad.operation=WR_RADIO_CLOSE;
  assert(wr_iot_mbss_close_checked(&dev,1,&bad)==-1&&
         !queue_stops&&!close_calls&&!down_calls);
  bad=t;bad.reset_kind=WR_RADIO_RESET_PDMA;
  assert(wr_iot_mbss_close_checked(&dev,1,&bad)==-1&&
         !queue_stops&&!close_calls&&!down_calls);
#endif
  if(mode==0){
#ifdef MT_MAC
#ifdef RTMP_PCI_SUPPORT
   dma_outstanding=1;
   assert(wr_iot_mbss_close_checked(&dev,1,&t)==-1&&
          r->close_stage==2&&!down_calls&&refs==1);
   dma_outstanding=0;
#endif
   txs_outstanding=1;
   assert(wr_iot_mbss_close_checked(&dev,1,&t)==-1&&
          r->close_stage==2&&!down_calls&&refs==1);
   txs_outstanding=0;
   assert(close_calls==1);
#endif
  }
  assert(wr_iot_mbss_close_checked(&dev,1,&t)==-1&&refs==1&&r->phase==WR_REF_CLOSING&&!held);
#ifdef MT_MAC
  if(mode==2){assert(r->close_stage==5&&!close_calls&&!down_calls);continue;}
#endif
  if(mode==1){assert(r->close_stage==5&&close_calls==1&&!down_calls);continue;}
  assert(r->close_stage==3&&close_calls==1&&down_calls==1);
  int prior_cr=cr_calls,prior_hnat=hnat_calls;
  bad=t;bad.serial++;assert(wr_iot_mbss_close_checked(&dev,1,&bad)==-1&&down_calls==1);
  down_result=0;assert(wr_iot_mbss_close_checked(&dev,1,&t)==0&&!refs&&r->phase==WR_REF_IDLE&&r->close_stage==4);
  assert(!a.wr_iot_transition.busy&&a.wr_iot_transition.retired_serial==t.serial);
  assert(close_calls==1&&cr_calls==prior_cr&&hnat_calls==prior_hnat&&down_calls==2);
  assert(wr_iot_mbss_close_checked(&dev,1,&t)==0&&!refs&&down_calls==2);
 }
 {
  /* If ticket retirement fails after checked DOWN, the reference and pin
   * must remain owned by the retained close path. */
  memset(&a,0,sizeof(a));a.net_dev=&main_dev;a.VirtualIfCnt=2;a.ApCfg.BssidNum=2;
  wr_iot_radio_transition_init(&a.wr_iot_transition);
  a.wr_iot_transition.phase=WR_RADIO_READY;
  struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];
  wr_iot_ref_init(r,&dev,1);r->family=WR_REF_FAMILY_MBSS;r->published=1;
  assert(wr_iot_ref_reserve(r,&dev,1,1));
  assert(wr_iot_ref_open_finish(r,&dev,1,1,1));
  set_main_owner(&a,&main_dev);
  assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==0);
  refs=1;cr_result=close_result=down_result=0;
  invalidate_epoch_on_down=1;
  assert(wr_iot_mbss_close_checked(&dev,generation,&t)==-1);
  assert(refs==1&&r->phase==WR_REF_CLOSING&&r->close_stage==3&&
         a.wr_iot_transition.busy==WR_RADIO_BSS_CLOSE);
  invalidate_epoch_on_down=0;
 }
#ifdef WR_IOT_V40
 {
  /* A corrupted/invalidated owner after vendor DOWN must not retire the
   * ticket before the original module reference is accounted for. */
  memset(&a,0,sizeof(a));a.net_dev=&main_dev;a.VirtualIfCnt=2;a.ApCfg.BssidNum=2;
  wr_iot_radio_transition_init(&a.wr_iot_transition);
  a.wr_iot_transition.phase=WR_RADIO_READY;
  struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];
  wr_iot_ref_init(r,&dev,1);r->family=WR_REF_FAMILY_MBSS;r->published=1;
  assert(wr_iot_ref_reserve(r,&dev,1,1));
  assert(wr_iot_ref_open_finish(r,&dev,1,1,1));
  set_main_owner(&a,&main_dev);
  assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==0);
  refs=1;cr_result=close_result=down_result=0;
  invalidate_token_on_down=1;
  assert(wr_iot_mbss_close_checked(&dev,generation,&t)==-1);
  assert(refs==1&&r->phase==WR_REF_CLOSING&&r->close_stage==3&&
         a.wr_iot_transition.busy==WR_RADIO_BSS_CLOSE&&
         a.wr_iot_transition.retired_serial!=t.serial);
  invalidate_token_on_down=0;
 }
 {
  /* An unclaimed count writer during vendor DOWN cannot be accepted as a
   * successful MBSS close, even when the vendor call reports success. */
  memset(&a,0,sizeof(a));a.net_dev=&main_dev;a.VirtualIfCnt=2;a.ApCfg.BssidNum=2;
  wr_iot_radio_transition_init(&a.wr_iot_transition);
  a.wr_iot_transition.phase=WR_RADIO_READY;
  struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];
  wr_iot_ref_init(r,&dev,1);r->family=WR_REF_FAMILY_MBSS;r->published=1;
  assert(wr_iot_ref_reserve(r,&dev,1,1));
  assert(wr_iot_ref_open_finish(r,&dev,1,1,1));
  set_main_owner(&a,&main_dev);
  assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==0);
  refs=1;cr_result=close_result=down_result=0;
  inflate_count_on_down=1;
  assert(wr_iot_mbss_close_checked(&dev,generation,&t)==-1);
  assert(refs==1&&r->phase==WR_REF_CLOSING&&r->close_stage==3&&
         a.wr_iot_transition.busy==WR_RADIO_BSS_CLOSE&&
         a.wr_iot_transition.retired_serial!=t.serial&&a.VirtualIfCnt==2);
  inflate_count_on_down=0;
 }
#endif
 {
  /* Inject slot reuse during an unlocked vendor call. The old close must
   * refuse the next stage without mutating the new registration. */
  memset(&a,0,sizeof(a));a.net_dev=&main_dev;a.VirtualIfCnt=2;a.ApCfg.BssidNum=2;
  wr_iot_radio_transition_init(&a.wr_iot_transition);
  a.wr_iot_transition.phase=WR_RADIO_UNVERIFIED;
  a.wr_iot_transition.serial=1;
  struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];
  wr_iot_ref_init(r,&dev,1);r->family=WR_REF_FAMILY_MBSS;r->published=1;
  assert(wr_iot_ref_reserve(r,&dev,1,1));
  assert(wr_iot_ref_open_finish(r,&dev,1,1,1));
  set_main_owner(&a,&main_dev);
  assert(wr_iot_mbss_begin_close(&dev,&t,&generation)==0&&generation==1);
  refs=1;cr_calls=close_calls=queue_stops=hnat_calls=down_calls=held=0;
  cr_result=close_result=0;reuse_on_close=1;
  assert(wr_iot_mbss_close_checked(&dev,1,&t)==-1);
  assert(r->generation==2&&r->published&&r->close_stage==0&&
         r->phase==WR_REF_IDLE&&close_calls==1&&!down_calls&&refs==1&&!held);
 }
 {
  struct wr_iot_radio_ticket extra;
  unsigned long extra_generation=99;
  struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];
  memset(&a,0,sizeof(a));a.net_dev=&main_dev;
  wr_iot_radio_transition_init(&a.wr_iot_transition);
  a.wr_iot_transition.phase=WR_RADIO_READY;
  wr_iot_ref_init(r,&dev,7);r->family=WR_REF_FAMILY_MBSS;
  assert(wr_iot_ref_reserve(r,&dev,7,1));
  assert(wr_iot_ref_open_finish(r,&dev,7,1,1));
  assert(wr_iot_mbss_begin_close(&dev,&extra,&extra_generation)==-1&&
         !extra_generation&&!a.wr_iot_transition.busy);
  r->published=1;
  assert(wr_iot_mbss_begin_close(&dev,&extra,&extra_generation)==-1&&
         !extra_generation&&!a.wr_iot_transition.busy);
  a.VirtualIfCnt=2;
  assert(wr_iot_mbss_begin_close(&dev,&extra,&extra_generation)==-1&&
         !extra_generation&&!a.wr_iot_transition.busy);
  set_main_owner(&a,&main_dev);
  assert(wr_iot_mbss_begin_close(&dev,&extra,&extra_generation)==0&&
         extra_generation==7);
  extra_generation=99;
  assert(wr_iot_mbss_begin_close(&dev,&bad,&extra_generation)==-1&&
         !extra_generation&&a.wr_iot_transition.busy==WR_RADIO_BSS_CLOSE);
 }
 return 0;
}
