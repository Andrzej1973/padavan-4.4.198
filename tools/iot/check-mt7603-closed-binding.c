#include <assert.h>
#include <stdio.h>
#include <errno.h>
#include "mbss-closed-probe.h"
#include "driver-api-owner.h"
typedef int INT;typedef unsigned long ULONG;
#include "beacon-producer-gate.h"
typedef unsigned int UINT32;
typedef struct device {int running;} *PNET_DEV;
typedef struct adapter {
 int mt7603,BcnRingLock,wr_iot_transition_lock,wr_iot_ticket_wait;
 unsigned wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[3];
 struct wr_iot_driver_owner wr_iot_driver_owner;
 unsigned flags;PNET_DEV net_dev;
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
#define WDEV_NUM_MAX 2
#define VIRTUAL_IF_NUM(ad) 1U
#define RTMP_IRQ_LOCK(lock,flags) do{(flags)=0;assert(!*(lock));*(lock)=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(flags);assert(*(lock));*(lock)=0;}while(0)
#define wake_up_all(queue) (++*(queue))
static int rtnl=1;
static int rtnl_is_locked(void){return rtnl;}
static unsigned queue,tbtt;static int dma,txs,drift;
static int netif_running(PNET_DEV dev){assert(dev);return dev->running;}
static void read_reg(PRTMP_ADAPTER ad,unsigned address,unsigned *out){
 assert(ad->BcnRingLock&&!ad->wr_iot_transition_lock);assert(address==ARB_BCNQCR0||address==LPON_SBTOR1+4);
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
 if(drift==5)wr_iot_radio_request_reset(&ad->wr_iot_transition);
 if(drift==6)ad->wr_iot_transition.serial++;
 return txs;
}
#include "mt7603-closed-observe.h"
#include "mt7603-closed-probe-binding.inc"
int main(void){
 for(unsigned fault=0;fault<9;fault++){
  struct device main_dev={1},iot={0};struct adapter ad={.mt7603=1,.flags=3,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  struct wr_iot_mbss_closed_probe probe={0};unsigned long sequence=0;
  ad.ApCfg.MBSSID[0].wdev.if_dev=&main_dev;ad.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;
  ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  struct wr_iot_interface_ref *m=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&iot,WR_REF_FAMILY_MBSS);
  m->published=r->published=1;m->phase=WR_REF_OWNED;m->last_token=1;
  r->last_token=2;r->close_serial=3;r->close_epoch=ad.wr_iot_transition.epoch;r->close_vendor_count=2;r->close_stage=4;
  queue=1;tbtt=0;dma=txs=drift=0;rtnl=1;
  switch(fault){
   case 1:dma=1;break;case 2:drift=3;break;case 3:ad.wr_iot_control_users=1;break;
   case 4:ad.wr_iot_driver_owner.active=1;break;case 5:drift=5;break;
   case 6:drift=6;break;case 7:probe.active=1;break;case 8:rtnl=0;break;
  }
  int result=wr_iot_mt7603_closed_probe(&ad,&iot,&probe,2,2,3);
  if(!fault)assert(result==0);
  else if(fault==1||fault==2||fault==5)assert(result==-EAGAIN&&!probe.active);
  else if(fault==6)assert(result==-EUCLEAN&&probe.active&&ad.wr_iot_control_poisoned&&ad.wr_iot_transition.busy);
  else assert(result==-EBUSY);
  assert(!ad.BcnRingLock&&!ad.wr_iot_transition_lock);
  if(fault==0||fault==1||fault==2||fault==5)assert(ad.wr_iot_ticket_wait==1);
  else assert(!ad.wr_iot_ticket_wait);
  if(fault==5)assert(ad.wr_iot_transition.reset_pending);
  if(fault==1||fault==2)assert(ad.wr_iot_transition.phase==WR_RADIO_READY&&ad.wr_iot_transition.main_ready);
 }
 puts("PASS actual closed probe binding: serialized receipt/readback, negative IoT observation preserves Main, reset invalidates, foreign ticket retains poisoned context, wake outside locks. Mock MMIO; no RF/teardown proof.");return 0;
}
