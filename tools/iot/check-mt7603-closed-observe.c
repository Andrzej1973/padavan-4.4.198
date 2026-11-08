#include <assert.h>
#include <stdio.h>
#include "beacon-producer-gate.h"
typedef unsigned int UINT32;
typedef struct device {int running;} *PNET_DEV;
typedef struct adapter {
 int mt7603,BcnRingLock;unsigned flags;PNET_DEV net_dev;
 struct {unsigned BssidNum;struct {struct {PNET_DEV if_dev;} wdev;struct {int bBcnSntReq;} bcn_buf;} MBSSID[3];} ApCfg;
 struct wr_iot_beacon_producer_gate wr_iot_beacon_gates[3];
} *PRTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->mt7603)
#define fRTMP_ADAPTER_START_UP 1U
#define fRTMP_ADAPTER_INTERRUPT_IN_USE 2U
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 4U
#define fRTMP_ADAPTER_RESET_IN_PROGRESS 8U
#define fRTMP_ADAPTER_NIC_NOT_EXIST 16U
#define fRTMP_ADAPTER_RADIO_OFF 32U
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 64U
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define ARB_BCNQCR0 0x100U
#define LPON_SBTOR1 0x200U
#define TBTT0_n_INT_EN 1U
#define PRE_TBTT0_n_INT_EN 2U
#define RTMP_SEM_LOCK(lock) do{assert(!*(lock));*(lock)=1;}while(0)
#define RTMP_SEM_UNLOCK(lock) do{assert(*(lock));*(lock)=0;}while(0)
static unsigned queue,tbtt;static int dma,txs,drift;
static int netif_running(PNET_DEV dev){assert(dev);return dev->running;}
static void read_reg(PRTMP_ADAPTER ad,unsigned address,unsigned *out){
 assert(ad->BcnRingLock);assert(address==ARB_BCNQCR0||address==LPON_SBTOR1+4);
 *out=address==ARB_BCNQCR0?queue:tbtt;
 if(drift==4&&address==LPON_SBTOR1+4)ad->flags|=fRTMP_ADAPTER_RESET_IN_PROGRESS;
}
#define RTMP_IO_READ32 read_reg
static int WrBeaconDmaOutstanding(PRTMP_ADAPTER ad,unsigned id){assert(!ad->BcnRingLock&&id==2);return dma;}
static int WrBeaconTxSOutstanding(PRTMP_ADAPTER ad,unsigned id){
 assert(!ad->BcnRingLock&&id==2);
 if(drift==1)ad->wr_iot_beacon_gates[2].generation++;
 if(drift==2)ad->wr_iot_beacon_gates[2].accepting=1;
 if(drift==3)ad->flags|=fRTMP_ADAPTER_RESET_IN_PROGRESS;
 return txs;
}
#include "mt7603-closed-observe.h"
int main(void){
 for(unsigned fault=0;fault<20;fault++){
  struct device main_dev={1},iot={0};struct adapter ad={.mt7603=1,.flags=3,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  ad.ApCfg.MBSSID[0].wdev.if_dev=&main_dev;ad.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;
  ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;ad.wr_iot_beacon_gates[2].generation=4;
  queue=1;tbtt=0;dma=txs=drift=0;
  switch(fault){
   case 1:ad.flags|=8;break;case 2:ad.flags=0;break;
   case 3:main_dev.running=0;break;case 4:iot.running=1;break;
   case 5:ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;break;
   case 6:ad.wr_iot_beacon_gates[2].accepting=1;break;
   case 7:ad.wr_iot_beacon_gates[2].active=1;break;
   case 8:queue|=1U<<17;break;case 9:queue=0;break;
   case 10:queue=0xffffffffU;break;case 11:tbtt=1;break;case 12:tbtt=2;break;
   case 13:dma=1;break;case 14:txs=1;break;case 15:dma=-1;break;
   case 16:drift=1;break;case 17:drift=2;break;case 18:drift=3;break;
   case 19:drift=4;break;
  }
  assert(wr_iot_mt7603_closed_config_observed(&ad,&iot)==(fault==0));
  assert(!ad.BcnRingLock);
 }
 puts("PASS closed configuration observer: main/IoT/gate/MMIO/DMA/TxS refusals, unlocked outstanding helpers, generation/reset drift rejected. Injected registers; not RF/FIFO/late-callback proof.");return 0;
}
