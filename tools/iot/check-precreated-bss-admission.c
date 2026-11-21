#include <assert.h>
#include <stdio.h>
struct device {int running;};
typedef struct {int mt7603;struct {unsigned BssidNum;struct {struct {struct device *if_dev;} wdev;struct {int bBcnSntReq;} bcn_buf;} MBSSID[4];} ApCfg;} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->mt7603)
#define RTMP_OS_NETDEV_STATE_RUNNING(dev) ((dev)->running)
#include "precreated-bss-admission.h"
int main(void){
 RTMP_ADAPTER ad={.mt7603=1};struct device dev={0};
 for(unsigned count=0;count<6;count++)for(unsigned exists=0;exists<2;exists++)for(unsigned running=0;running<2;running++)for(unsigned beacon=0;beacon<2;beacon++){
  ad.ApCfg.BssidNum=count;dev.running=running;ad.ApCfg.MBSSID[2].wdev.if_dev=exists?&dev:NULL;ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=beacon;
  assert(wr_iot_precreated_bss_admitted(&ad,0));assert(wr_iot_precreated_bss_admitted(&ad,1));
  assert(wr_iot_precreated_bss_admitted(&ad,2)==(count>=3&&count<=4&&exists&&running&&beacon));
 }
 ad.mt7603=0;assert(wr_iot_precreated_bss_admitted(&ad,2));
 puts("PASS reserved third BSS admission: count/device/running/beacon gates; Main/Guest/other chip unchanged. Snapshot only, no concurrent close/RX lifetime proof.");return 0;
}
