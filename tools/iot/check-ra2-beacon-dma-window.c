#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "beacon-producer-gate.h"
typedef uint32_t UINT32;
typedef int INT;
struct device {int running;};
typedef struct {
 int chip,BcnRingLock;
 struct {unsigned BeaconPeriod;} CommonCfg;
 struct {unsigned BssidNum;struct {
  struct {struct device *if_dev;} wdev;
  struct {int bBcnSntReq,bcn_state;} bcn_buf;
  int timer_loop;unsigned long WriteBcnDoneTime[4];
 } MBSSID[4];} ApCfg;
 struct wr_iot_beacon_producer_gate wr_iot_beacon_gates[3];
} RTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->chip==0x7603)
#define netif_running(dev) ((dev)->running)
#define BCN_TX_DMA_DONE 2
#define BCN_TX_IDLE 0
#include "ra2-beacon-dma-window.h"
static int dma_result,txs_result,revoke_on_snapshot;
static UINT32 tsf;
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *ad,unsigned bss)
{
 assert(!ad->BcnRingLock&&bss==2);
 if(revoke_on_snapshot)assert(wr_iot_beacon_gate_revoke(&ad->wr_iot_beacon_gates[2],1));
 return dma_result;
}
static int WrBeaconTxSOutstanding(RTMP_ADAPTER *ad,unsigned bss)
{assert(!ad->BcnRingLock&&bss==2);return txs_result;}
static void AsicGetTsfTime(RTMP_ADAPTER *ad,UINT32 *high,UINT32 *low)
{assert(!ad->BcnRingLock);*high=0;*low=tsf;}
#define RTMP_SEM_LOCK(lock) do{assert(!*(lock));*(lock)=1;}while(0)
#define RTMP_SEM_UNLOCK(lock) do{assert(*(lock));*(lock)=0;}while(0)
#include "ra2-beacon-periodic-experiment.inc"
int main(void)
{
 for(unsigned fault=0;fault<20;fault++){
  RTMP_ADAPTER ad={.chip=0x7603,.CommonCfg.BeaconPeriod=100,.ApCfg.BssidNum=3};
  struct device dev={1};struct wr_iot_beacon_producer_ticket ticket={0};
  UINT32 now=102400;int dma=0,txs=0;
  ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
  ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_DMA_DONE;
  assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[2],1));
  assert(wr_iot_beacon_gate_begin(&ad.wr_iot_beacon_gates[2],1,&ticket));
  switch(fault){
  case 1:now--;break;
  case 2:dma=1;break;
  case 3:dma=-1;break;
  case 4:txs=1;break;
  case 5:txs=-1;break;
  case 6:ad.ApCfg.BssidNum=4;break;
  case 7:dev.running=0;break;
  case 8:ad.ApCfg.MBSSID[2].timer_loop=-1;break;
  case 9:ad.ApCfg.MBSSID[2].timer_loop=4;break;
  case 10:ad.CommonCfg.BeaconPeriod=0;break;
  case 11:ad.wr_iot_beacon_gates[2].active=2;break;
  case 12:ticket.generation++;break;
  case 13:assert(wr_iot_beacon_gate_revoke(&ad.wr_iot_beacon_gates[2],1));break;
  case 14:ad.ApCfg.MBSSID[2].WriteBcnDoneTime[0]=0xffff0000U;now=36864;break;
  case 15:ad.ApCfg.MBSSID[2].WriteBcnDoneTime[0]=now+1;break;
  case 16:now=0x80000000U;break;
  case 17:ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_IDLE;dev.running=0;break;
  case 18:ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_IDLE;ad.ApCfg.MBSSID[2].wdev.if_dev=NULL;break;
  case 19:ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_IDLE;ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;break;
  }
  RTMP_ADAPTER before=ad;
  RTMP_ADAPTER periodic=ad;
  dma_result=dma;txs_result=txs;tsf=now;revoke_on_snapshot=0;
  assert(wr_iot_bcn_periodic_ready(&periodic,2,&ticket)==(fault==0||fault==14));
  if(fault==0||fault==14)periodic.ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_DMA_DONE;
  assert(!memcmp(&periodic,&before,sizeof(periodic)));
  if(!fault){
   revoke_on_snapshot=1;
   assert(!wr_iot_bcn_periodic_ready(&periodic,2,&ticket));
   assert(periodic.ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_DMA_DONE&&!periodic.BcnRingLock);
   revoke_on_snapshot=0;
   assert(wr_iot_bcn_periodic_ready(&ad,1,&ticket)); /* Guest bypass unchanged. */
  }
  assert(wr_iot_ra2_beacon_dma_window(&ad,&ticket,now,dma,txs)==(fault==0||fault==14));
  assert(!memcmp(&before,&ad,sizeof(ad)));
  int expected=fault==0||fault==14;
  assert(wr_iot_ra2_beacon_prepare_next(&ad,&ticket,now,dma,txs)==expected);
  if(expected)before.ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_IDLE;
  assert(!memcmp(&before,&ad,sizeof(ad)));
  /* A second hand-off cannot turn one completed publication into two. */
  assert(!wr_iot_ra2_beacon_prepare_next(&ad,&ticket,now,dma,txs));
  assert(!memcmp(&before,&ad,sizeof(ad)));
 }
 /* A retained DMA_DONE buffer can pass through a closed producer generation
  * and wait for the next natural window after the caller reopens admission.
  * This models gate/pacing only, not the API CLOSE-owner release operation. */
 {
  RTMP_ADAPTER ad={.chip=0x7603,.CommonCfg.BeaconPeriod=100,.ApCfg.BssidNum=3};
  struct device dev={1};
  struct wr_iot_beacon_producer_ticket old={0},next={0};
  struct wr_iot_beacon_producer_gate *gate=&ad.wr_iot_beacon_gates[2];
  ad.ApCfg.MBSSID[2].wdev.if_dev=&dev;
  ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=BCN_TX_DMA_DONE;
  ad.ApCfg.MBSSID[2].WriteBcnDoneTime[0]=1000;
  dma_result=txs_result=revoke_on_snapshot=0;
  assert(wr_iot_beacon_gate_open(gate,1));
  assert(wr_iot_beacon_gate_begin(gate,1,&old));
  assert(wr_iot_beacon_gate_revoke(gate,1));
  assert(!wr_iot_beacon_gate_open(gate,2));
  assert(wr_iot_beacon_gate_end(gate,&old));
  dev.running=0;ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;
  assert(wr_iot_beacon_gate_drained(gate,1));
  assert(wr_iot_beacon_gate_open(gate,2));
  assert(wr_iot_beacon_gate_begin(gate,2,&next));
  assert(!wr_iot_beacon_gate_submit(gate,&old));
  tsf=103400;
  assert(!wr_iot_bcn_periodic_ready(&ad,2,&next));
  dev.running=1;ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  tsf=103399;
  assert(!wr_iot_bcn_periodic_ready(&ad,2,&next));
  assert(ad.ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_DMA_DONE);
  tsf=103400;
  assert(wr_iot_bcn_periodic_ready(&ad,2,&next));
  assert(ad.ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_IDLE);
  assert(wr_iot_beacon_gate_end(gate,&next));
 }
 puts("PASS unbound ra2 pacing: DMA/TxS unknowns, exact period, TSF wrap/backward ambiguity, exclusive producer and revoke; no RF or epoch proof");
 return 0;
}
