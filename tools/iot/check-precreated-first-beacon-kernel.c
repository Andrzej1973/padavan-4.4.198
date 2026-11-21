#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "beacon-producer-gate.h"
#include "precreated-first-beacon.h"
#ifndef WR_IOT_OTHER_CHIP
#define MT7603 1
#endif
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define HIF_MT 1
#define IS_MT7603(ad) ((ad)->mt)
typedef struct {
 int mt;struct {int hif_type;} chipCap;
 struct {int BssidNum;struct {struct {void *if_dev;} wdev;} MBSSID[3];} ApCfg;
 struct wr_iot_beacon_producer_gate wr_iot_beacon_gates[3];
 struct wr_iot_first_beacon wr_iot_first_beacon;
 struct wr_iot_first_beacon_identity wr_iot_first_beacon_capture;
} RTMP_ADAPTER;
#include "precreated-first-beacon-kernel.h"
int main(void)
{
 int dev,other;
 struct wr_iot_first_beacon_identity id={&dev,1,7,3,4,5};
 RTMP_ADAPTER ad={0};ad.mt=1;ad.chipCap.hif_type=HIF_MT;
 ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
 assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[2],7));
#ifdef WR_IOT_OTHER_CHIP
 assert(!wr_iot_first_beacon_arm_locked(&ad,&id,1));
 wr_iot_first_beacon_capture_locked(&ad,2,7);
 assert(!wr_iot_first_beacon_published_locked(&ad,2));
 (void)other;
#else
 assert(!wr_iot_first_beacon_arm_locked(&ad,&id,0));
 ad.wr_iot_beacon_gates[2].active=1;
 assert(!wr_iot_first_beacon_arm_locked(&ad,&id,1));
 ad.wr_iot_beacon_gates[2].active=0;
 for(int fault=0;fault<9;fault++){
  memset(&ad.wr_iot_first_beacon,0,sizeof(ad.wr_iot_first_beacon));
  ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
  ad.wr_iot_beacon_gates[2].generation=7;
  ad.wr_iot_beacon_gates[2].accepting=1;ad.wr_iot_beacon_gates[2].active=0;
  assert(wr_iot_first_beacon_arm_locked(&ad,&id,1));
  ad.wr_iot_beacon_gates[2].active=1;
  wr_iot_first_beacon_capture_locked(&ad,2,7);
  assert(ad.wr_iot_first_beacon_capture.request_generation==id.request_generation);
  if(fault==2)ad.wr_iot_beacon_gates[2].accepting=0;
  if(fault==3)ad.wr_iot_beacon_gates[2].generation++;
  if(fault==4)assert(wr_iot_first_beacon_expire(&ad.wr_iot_first_beacon,&id));
  if(fault==5)ad.ApCfg.MBSSID[2].wdev.if_dev=&other;
  if(fault==8)ad.ApCfg.BssidNum=4;
  /* Fault1 models a rejected pre-publication kickout: hook is never called. */
  int published=fault==1?0:wr_iot_first_beacon_published_locked(&ad,fault==6?1:2);
  assert(published==(fault==0||fault==7));
  assert(wr_iot_first_beacon_finish(&ad.wr_iot_first_beacon,&id,fault==7?0:1)==(fault==0));
 }
 /* An expired old producer cannot acquire a fresh activation identity. */
 memset(&ad.wr_iot_first_beacon,0,sizeof(ad.wr_iot_first_beacon));
 ad.ApCfg.BssidNum=3;ad.wr_iot_beacon_gates[2].active=0;
 assert(wr_iot_first_beacon_arm_locked(&ad,&id,1));
 ad.wr_iot_beacon_gates[2].active=1;wr_iot_first_beacon_capture_locked(&ad,2,7);
 assert(wr_iot_first_beacon_expire(&ad.wr_iot_first_beacon,&id));
 id.request_generation++;
 assert(!wr_iot_first_beacon_arm_locked(&ad,&id,1));
 ad.wr_iot_beacon_gates[2].active=0;
 assert(wr_iot_first_beacon_arm_locked(&ad,&id,1));
 ad.wr_iot_beacon_gates[2].active=1;
 assert(!wr_iot_first_beacon_published_locked(&ad,2));
 wr_iot_first_beacon_capture_locked(&ad,2,7);
 assert(wr_iot_first_beacon_published_locked(&ad,2));
 assert(wr_iot_first_beacon_finish(&ad.wr_iot_first_beacon,&id,1));
#endif
 puts("PASS first-beacon kernel hooks: captured identity, checked host publication, refused stale/cancelled/foreign generations; no RF or driver endpoint proof.");
 return 0;
}
