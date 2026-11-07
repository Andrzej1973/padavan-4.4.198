#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned int UINT32;
struct device {int running;};
typedef struct device *PNET_DEV;
typedef struct adapter {unsigned int flags;int chip,BcnRingLock;struct device *net_dev;
 struct {unsigned int BssidNum;struct {struct {struct device *if_dev;} wdev;
 struct {int bBcnSntReq;} bcn_buf;} MBSSID[3];} ApCfg;} *PRTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->chip==0x7603)
#define netif_running(dev) ((dev)->running)
#define fRTMP_ADAPTER_START_UP 1U
#define fRTMP_ADAPTER_INTERRUPT_IN_USE 2U
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 4U
#define fRTMP_ADAPTER_RESET_IN_PROGRESS 8U
#define fRTMP_ADAPTER_NIC_NOT_EXIST 16U
#define fRTMP_ADAPTER_RADIO_OFF 32U
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 64U
#define RTMP_TEST_FLAG(ad,mask) ((ad)->flags&(mask))
#define RTMP_SEM_LOCK(lock) (assert(!*(lock)),*(lock)=1)
#define RTMP_SEM_UNLOCK(lock) (assert(*(lock)),*(lock)=0)
#define ARB_BCNQCR0 0x100U
static unsigned int reg_value,inject_flag;static int reads;
#define RTMP_IO_READ32(ad,address,value) do {assert((ad)->BcnRingLock&&(address)==ARB_BCNQCR0);reads++;*(value)=reg_value;(ad)->flags|=inject_flag;} while(0)
#include "mt7603-main-observe.h"
int main(void){
 struct adapter a;struct device main_dev={1},iot={0};
 for(int mode=0;mode<18;mode++){
  memset(&a,0,sizeof(a));a.flags=3;a.chip=0x7603;a.net_dev=&main_dev;
  a.ApCfg.BssidNum=3;a.ApCfg.MBSSID[0].wdev.if_dev=&main_dev;
  a.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;a.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  main_dev.running=1;iot.running=0;reads=0;reg_value=1;inject_flag=0;
  if(mode==1)a.chip=0;
  if(mode>=2&&mode<=7)a.flags|=1U<<mode;
  if(mode==8)reg_value=0xffffffffU;
  if(mode==9)reg_value=0;
  if(mode==10)reg_value=1U|(1U<<(2U+15U));
  if(mode==11)iot.running=1; /* __dev_open sets START before ndo_open */
  if(mode==12)a.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  if(mode==13)a.ApCfg.BssidNum=4;
  if(mode==14)main_dev.running=0;
  if(mode==15)a.flags=0;
  if(mode==16)inject_flag=fRTMP_ADAPTER_RESET_IN_PROGRESS;
  if(mode==17)reg_value=5; /* bit 2 is not the IoT beacon-queue bit */
  /* Mode 7 tests an unrelated flag, which must not cause rejection. */
  assert(wr_iot_mt7603_main_config_observed(&a)==
   (mode==0||mode==7||mode==11||mode==17));
  assert(!a.BcnRingLock&&reads<=1);
 }
 for(int mode=0;mode<10;mode++){
  unsigned int bss_id=mode==0?1U:2U;
  memset(&a,0,sizeof(a));a.flags=3;a.chip=0x7603;a.net_dev=&main_dev;
  a.ApCfg.BssidNum=3;a.ApCfg.MBSSID[0].wdev.if_dev=&main_dev;
  a.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;
  a.ApCfg.MBSSID[1].wdev.if_dev=&iot;
  a.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  a.ApCfg.MBSSID[1].bcn_buf.bBcnSntReq=1;
  a.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  main_dev.running=iot.running=1;reads=0;inject_flag=0;
  reg_value=1U|(1U<<(bss_id+15U));
  if(mode==2)reg_value=1U;
  if(mode==4)a.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;
  if(mode==5)inject_flag=fRTMP_ADAPTER_RESET_IN_PROGRESS;
  if(mode==6)reg_value=1U<<(bss_id+15U);
  if(mode==7)iot.running=0;
  if(mode==8)a.ApCfg.BssidNum=2;
  if(mode==9)bss_id=3U;
  assert(wr_iot_mt7603_bss_config_observed(&a,
   mode==3?&main_dev:&iot,bss_id)==(mode==0||mode==1));
  assert(!a.BcnRingLock&&reads<=1);
 }
 assert(!wr_iot_mt7603_main_config_observed(NULL));
 puts("PASS MT7603 config observers: main/preopen and guest/IoT postopen request/queue readback; injected MMIO, not RF proof");return 0;
}
