#include <radio-transition.h>
#include <interface-registry.h>
#include <assert.h>
#include <stdio.h>
#include <string.h>

#define WDEV_NUM_MAX 2
typedef int INT;
typedef void VOID;
typedef unsigned long ULONG;
struct adapter;
typedef struct device {struct adapter *adapter;} *PNET_DEV;
typedef struct adapter {
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
 int wr_iot_transition_lock,wr_iot_ticket_wait,VirtualIfCnt;
 PNET_DEV net_dev;
 struct {int BssidNum;struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];} ApCfg;
} *PRTMP_ADAPTER;
static int locked,readback=1,reset_during_read,reset_during_publish;
static int main_down_during_publish;
static int extra_count,raw_error,ready_calls,down_calls,steering_ready;
#define BAND_STEERING 1
#define IS_MT7603(ad) (1)
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->adapter)
#define RTMP_IRQ_LOCK(lock,flags) ((void)(lock),(flags)=0,assert(!locked),locked=1)
#define RTMP_IRQ_UNLOCK(lock,flags) ((void)(lock),(void)(flags),assert(locked),locked=0)
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define wake_up_all(wait) ((void)(wait))
static VOID wr_iot_mbss_publish_ready(PRTMP_ADAPTER ad,PNET_DEV dev,INT id){
 assert(!locked&&ad&&dev&&(id==1||id==2));ready_calls++;steering_ready=1;
 if(reset_during_publish)wr_iot_radio_request_reset(&ad->wr_iot_transition);
 if(main_down_during_publish)wr_iot_radio_main_down(&ad->wr_iot_transition);
}
static VOID wr_iot_mbss_publish_down(PRTMP_ADAPTER ad,PNET_DEV dev,INT id){
 assert(!locked&&ad&&dev&&(id==1||id==2));down_calls++;steering_ready=0;
}
static int main_observe(PRTMP_ADAPTER ad){(void)ad;assert(!locked);return 1;}
static int bss_observe(PRTMP_ADAPTER ad,PNET_DEV dev,unsigned int id){
 (void)dev;assert(!locked&&(id==1U||id==2U));
 if(reset_during_read)wr_iot_radio_request_reset(&ad->wr_iot_transition);
 return readback;
}
#define WR_IOT_MBSS_OBSERVE_MAIN(ad) main_observe(ad)
#define WR_IOT_MBSS_OBSERVE_BSS(ad,dev,id) bss_observe((ad),(dev),(id))
static INT wr_iot_mbss_open_raw(PNET_DEV dev
#ifdef WR_IOT_V40
 ,const struct wr_iot_radio_ticket *ticket,unsigned long generation
#endif
 ){
#ifdef WR_IOT_V40
 assert(ticket&&generation);
#endif
 assert(!locked);
 if(raw_error==-2)return -2;
 dev->adapter->VirtualIfCnt+=1+extra_count;
 return raw_error;
}
#ifdef WR_IOT_V40
#include "wr-iot-mbss-open-admission.inc"
#else
#include "mbss-open-admission.inc"
#endif

static void setup(struct adapter *ad,struct device *main_dev,
 struct device *guest_dev,struct device *iot_dev){
 unsigned long sequence=0;
 struct wr_iot_interface_ref *main_ref,*guest_ref,*iot_ref;
 memset(ad,0,sizeof(*ad));
 main_dev->adapter=guest_dev->adapter=iot_dev->adapter=ad;
 ad->net_dev=main_dev;ad->VirtualIfCnt=1;ad->ApCfg.BssidNum=3;
 ad->ApCfg.MBSSID[0].wdev.if_dev=main_dev;
 ad->ApCfg.MBSSID[1].wdev.if_dev=guest_dev;
 ad->ApCfg.MBSSID[2].wdev.if_dev=iot_dev;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.phase=WR_RADIO_READY;
 ad->wr_iot_transition.main_ready=1;
 main_ref=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,
  &sequence,main_dev,WR_REF_FAMILY_MAIN);
 guest_ref=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,
  &sequence,guest_dev,WR_REF_FAMILY_MBSS);
 iot_ref=wr_iot_registry_add_family(ad->wr_iot_interface_refs,3,
  &sequence,iot_dev,WR_REF_FAMILY_MBSS);
 assert(main_ref&&guest_ref&&iot_ref);
 main_ref->phase=WR_REF_OWNED;
 main_ref->published=guest_ref->published=iot_ref->published=1;
 locked=reset_during_read=reset_during_publish=main_down_during_publish=0;
 extra_count=raw_error=0;
 ready_calls=down_calls=steering_ready=0;readback=1;
}
int main(void){
 struct adapter ad;
 struct device main_dev,guest_dev,iot_dev;
 setup(&ad,&main_dev,&guest_dev,&iot_dev);
 assert(MBSS_VirtualIF_Open(&guest_dev)==0);
 assert(ad.wr_iot_transition.phase==WR_RADIO_READY&&ad.wr_iot_transition.main_ready);
 assert(MBSS_VirtualIF_Open(&iot_dev)==0);
 assert(ad.VirtualIfCnt==3&&ad.wr_iot_transition.phase==WR_RADIO_READY&&ready_calls==2);

 setup(&ad,&main_dev,&guest_dev,&iot_dev);readback=0;
 assert(MBSS_VirtualIF_Open(&guest_dev)==0);
 assert(ad.wr_iot_transition.phase==WR_RADIO_UNVERIFIED&&ready_calls==0);
 assert(MBSS_VirtualIF_Open(&iot_dev)==-1);

 setup(&ad,&main_dev,&guest_dev,&iot_dev);extra_count=1;
 assert(MBSS_VirtualIF_Open(&guest_dev)==0);
 assert(ad.wr_iot_transition.phase==WR_RADIO_UNVERIFIED&&ready_calls==0);

 setup(&ad,&main_dev,&guest_dev,&iot_dev);reset_during_read=1;
 assert(MBSS_VirtualIF_Open(&guest_dev)==0);
 assert(ad.wr_iot_transition.reset_pending&&!ad.wr_iot_transition.main_ready&&ready_calls==0);

 setup(&ad,&main_dev,&guest_dev,&iot_dev);reset_during_publish=1;
 assert(MBSS_VirtualIF_Open(&guest_dev)==0);
 assert(ad.wr_iot_transition.reset_pending&&!ad.wr_iot_transition.main_ready);
 assert(ready_calls==1&&down_calls==1&&!steering_ready);

 setup(&ad,&main_dev,&guest_dev,&iot_dev);main_down_during_publish=1;
 assert(MBSS_VirtualIF_Open(&guest_dev)==0);
 assert(ad.wr_iot_transition.main_inhibited&&!ad.wr_iot_transition.main_ready);
 assert(ready_calls==1&&down_calls==1&&!steering_ready);

 setup(&ad,&main_dev,&guest_dev,&iot_dev);raw_error=-3;
 assert(MBSS_VirtualIF_Open(&guest_dev)==-1);
 assert(ad.VirtualIfCnt==2&&ad.wr_iot_interface_refs[1].phase==WR_REF_OWNED);
 assert(ad.wr_iot_transition.phase==WR_RADIO_FAULT&&ready_calls==0);
 assert(MBSS_VirtualIF_Open(&iot_dev)==-1);

 setup(&ad,&main_dev,&guest_dev,&iot_dev);raw_error=-2;
 assert(MBSS_VirtualIF_Open(&guest_dev)==-1);
 assert(ad.VirtualIfCnt==1&&ad.wr_iot_interface_refs[1].phase==WR_REF_UNCERTAIN_OPEN&&ready_calls==0);
 puts("PASS MBSS post-open: guest/IoT, readback/count/reset, distinct partial-open ownership");
 return 0;
}
