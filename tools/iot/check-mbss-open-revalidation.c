#include "radio-transition.h"
#include "interface-reference.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

typedef int INT;
typedef unsigned long ULONG;
struct device;
typedef struct adapter {
 int wr_iot_transition_lock;
 struct wr_iot_radio_transition wr_iot_transition;
 struct device *net_dev;
 struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct {int BssidNum;struct {struct {struct device *if_dev;} wdev;} MBSSID[3];} ApCfg;
} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;

static int held,raw_calls,observed,mode;
#define WDEV_NUM_MAX 1
#define IS_MT7603(ad) (1)
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define RTMP_IRQ_LOCK(lock,flags) do {(void)(lock);(flags)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do {(void)(lock);(void)(flags);assert(held);held=0;}while(0)
static int observe_main(PRTMP_ADAPTER ad){
 assert(!held&&ad->wr_iot_transition.busy==WR_RADIO_BSS_OPEN);
 observed++;
 if(mode==3)wr_iot_radio_request_reset(&ad->wr_iot_transition);
 if(mode==4)wr_iot_radio_main_down(&ad->wr_iot_transition);
 if(mode==5)wr_iot_radio_request_close(&ad->wr_iot_transition);
 return mode!=2;
}
#define WR_IOT_MBSS_OBSERVE_MAIN(ad) observe_main(ad)
static INT wr_iot_mbss_open_raw(PNET_DEV dev){
 assert(dev&&!held&&dev->ad->wr_iot_transition.busy==WR_RADIO_BSS_OPEN);
 raw_calls++;return 0;
}
#include "mbss-open-admission.inc"

int main(void){
 struct adapter ad;struct device main_dev,dev;
 for(mode=0;mode<7;mode++){
  memset(&ad,0,sizeof(ad));main_dev.ad=dev.ad=&ad;
  ad.net_dev=&main_dev;ad.ApCfg.BssidNum=3;
  ad.ApCfg.MBSSID[2].wdev.if_dev=mode==6?&main_dev:&dev;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);
  ad.wr_iot_transition.phase=mode==1?WR_RADIO_UNVERIFIED:WR_RADIO_READY;
  ad.wr_iot_transition.main_ready=mode!=1;
  wr_iot_ref_init(&ad.wr_iot_interface_refs[0],&dev,1);
  ad.wr_iot_interface_refs[0].published=1;
  held=raw_calls=observed=0;
  INT ret=MBSS_VirtualIF_Open(&dev);
  assert(!held&&!ad.wr_iot_transition.busy);
  if(mode==0||mode==6){
   assert(ret==0&&raw_calls==1&&ad.wr_iot_interface_refs[0].phase==WR_REF_OWNED);
  }else{
   assert(ret==-1&&raw_calls==0&&ad.wr_iot_interface_refs[0].phase==WR_REF_IDLE);
  }
  assert(observed==(mode==1||mode==6?0:1));
  if(mode==2)assert(ad.wr_iot_transition.main_ready);
  if(mode==3)assert(ad.wr_iot_transition.reset_pending&&!ad.wr_iot_transition.main_ready);
  if(mode==4)assert(ad.wr_iot_transition.main_inhibited&&!ad.wr_iot_transition.main_ready);
  if(mode==5)assert(ad.wr_iot_transition.phase==WR_RADIO_CLOSING);
 }
 puts("PASS IoT BSS open revalidation: observation, stale intent refusal, guest bypass; injected driver IO");
 return 0;
}
