#include <assert.h>
#include <stdio.h>
#include <string.h>
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
 struct wr_iot_mbss_closed_probe wr_iot_closed_probe;
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
typedef struct adapter RTMP_ADAPTER;
struct ifreq {void *ifr_data;};struct netspace {void *user_ns;};
static struct netspace space;static int permitted=1,copy_in_error,copy_out_error;
static unsigned copies_in,copies_out;
#define CAP_NET_ADMIN 12
static struct netspace *dev_net(PNET_DEV dev){assert(dev);return &space;}
static int ns_capable(void *ns,int cap){assert(ns==space.user_ns&&cap==12);return permitted;}
static unsigned long copy_from_user(void *out,const void *in,unsigned long n){assert(n==64);copies_in++;if(copy_in_error)return 1;memcpy(out,in,n);return 0;}
static unsigned long copy_to_user(void *out,const void *in,unsigned long n){assert(n==64);copies_out++;if(copy_out_error)return 1;memcpy(out,in,n);return 0;}
#include "driver-api-closed-entry.inc"
int main(void){
 for(unsigned fault=0;fault<13;fault++){
  struct device main_dev={1},iot={0};struct adapter ad={.mt7603=1,.flags=3,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  unsigned char id[16]={1},wire[64];struct ifreq rq={wire};unsigned long sequence=0;
  struct wr_iot_driver_closed_result response;
  ad.ApCfg.MBSSID[0].wdev.if_dev=&main_dev;ad.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq=1;ad.ApCfg.MBSSID[2].wdev.if_dev=&iot;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  ad.wr_iot_transition.serial=ad.wr_iot_transition.retired_serial=3;
  struct wr_iot_interface_ref *m=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&iot,WR_REF_FAMILY_MBSS);
  m->published=r->published=1;m->phase=WR_REF_OWNED;m->last_token=1;
  r->last_token=2;r->close_serial=3;r->close_epoch=1;r->close_vendor_count=2;r->close_stage=4;
  ad.wr_iot_driver_owner.receipt.device=&iot;ad.wr_iot_driver_owner.receipt.epoch=1;
  ad.wr_iot_driver_owner.receipt.generation=2;ad.wr_iot_driver_owner.receipt.open_token=2;
  ad.wr_iot_driver_owner.receipt.request_id[0]=1;ad.wr_iot_driver_owner.receipt.valid=1;
  permitted=rtnl=1;copy_in_error=copy_out_error=0;copies_in=copies_out=0;
  queue=1;tbtt=0;dma=txs=drift=0;
  switch(fault){
   case 1:permitted=0;break;case 2:id[0]=2;break;case 3:r->close_stage=3;break;
   case 4:ad.wr_iot_driver_owner.receipt.valid=0;break;case 5:ad.wr_iot_transition.epoch++;break;
   case 6:dma=1;break;case 7:queue|=1U<<17;break;case 8:copy_in_error=1;break;
   case 9:copy_out_error=1;break;case 10:copy_out_error=1;break;case 11:drift=6;break;case 12:drift=5;break;
  }
  assert(wr_iot_driver_closed_query_encode(wire,64,id));
  int result=wr_iot_driver_closed_ioctl(&ad,&iot,&rq);
  if(!fault){assert(!result&&wr_iot_driver_closed_decode(&response,id,wire,64));assert(response.adapter_epoch==1&&response.device_generation==2&&response.open_token==2&&response.close_serial==3);}
  else if(fault==1)assert(result==-EPERM&&!copies_in&&!copies_out);
  else if(fault==8||fault==9||fault==10)assert(result==-EFAULT);
  else if(fault==11)assert(result==-EUCLEAN&&ad.wr_iot_closed_probe.active&&ad.wr_iot_control_poisoned);
  else assert(result<0&&!copies_out);
  if(fault==10){copy_out_error=0;assert(wr_iot_driver_closed_query_encode(wire,64,id));assert(!wr_iot_driver_closed_ioctl(&ad,&iot,&rq));}
  assert(!ad.BcnRingLock&&!ad.wr_iot_transition_lock);
 }
 for(unsigned fault=0;fault<18;fault++){
  struct device main_dev={1},iot={0};struct adapter ad={.mt7603=1,.net_dev=&main_dev};
  unsigned char id[16]={1},wire[64];struct ifreq rq={wire};unsigned long sequence=0;
  struct wr_iot_driver_refusal_result out;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  struct wr_iot_interface_ref *m=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&iot,WR_REF_FAMILY_MBSS);
  m->published=r->published=1;m->phase=WR_REF_OWNED;r->last_token=2;r->open_unmutated=1;
  ad.wr_iot_driver_owner.refusal=(struct wr_iot_driver_open_receipt){.device=&iot,.epoch=1,.generation=2,.open_token=2,.request_id={1},.valid=1};
  permitted=rtnl=1;copy_in_error=copy_out_error=0;copies_in=copies_out=0;
  switch(fault){
   case 1:permitted=0;break;case 2:id[0]=2;break;case 3:r->open_unmutated=0;break;
   case 4:ad.wr_iot_driver_owner.refusal.valid=0;break;case 5:ad.wr_iot_transition.epoch++;break;
   case 6:ad.wr_iot_transition.reset_pending=1;break;case 7:r->phase=WR_REF_OWNED;break;
   case 8:copy_in_error=1;break;case 9:copy_out_error=1;break;
   case 10:ad.wr_iot_driver_owner.active=1;break;case 11:ad.wr_iot_closed_probe.active=1;break;
   case 12:ad.wr_iot_control_users=1;break;case 13:ad.wr_iot_driver_owner.poisoned=1;break;
   case 14:wr_iot_radio_main_down(&ad.wr_iot_transition);break;
   case 15:ad.wr_iot_transition.retiring=1;break;
   case 16:ad.wr_iot_transition.exhausted=1;break;
   case 17:ad.wr_iot_transition.pm_suspending=1;break;
  }
  assert(wr_iot_driver_refusal_query_encode(wire,64,id));
  int result=wr_iot_driver_closed_ioctl(&ad,&iot,&rq);
  if(!fault){
   assert(!result&&wr_iot_driver_refusal_decode(&out,id,wire,64));
   assert(out.adapter_epoch==1&&out.device_generation==2&&out.attempt_token==2);
   struct wr_iot_driver_closed_result closed;
   assert(!wr_iot_driver_closed_decode(&closed,id,wire,64));
  }else assert(result<0);
  if(fault==1)assert(!copies_in);
  assert(!ad.wr_iot_transition_lock&&!ad.BcnRingLock);
 }

 for(unsigned fault=0;fault<9;fault++){
  struct device main_dev={1},iot={0};struct adapter ad={.mt7603=1,.net_dev=&main_dev};
  unsigned char id[16]={1},wire[64];struct ifreq rq={wire};unsigned long sequence=0;
  struct wr_iot_driver_uncertain_result out;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);
  struct wr_iot_interface_ref *r=wr_iot_registry_add_family(ad.wr_iot_interface_refs,3,&sequence,&iot,WR_REF_FAMILY_MBSS);
  r->published=1;r->last_token=2;
  ad.wr_iot_driver_owner.poisoned=1;
  ad.wr_iot_driver_owner.uncertain_request_id[0]=1;
  ad.wr_iot_driver_owner.claim=(struct wr_iot_virtual_open_claim){.device=&iot,.epoch=1,.generation=r->generation,.serial=2,.operation=WR_RADIO_BSS_OPEN};
  permitted=rtnl=1;copy_in_error=copy_out_error=0;copies_in=copies_out=0;
  switch(fault){
   case 1:id[0]=2;break;case 2:ad.wr_iot_driver_owner.poisoned=0;break;
   case 3:ad.wr_iot_driver_owner.active=1;break;case 4:r->removing=1;break;
   case 5:ad.wr_iot_transition.epoch++;break;case 6:r->last_token++;break;
   case 7:permitted=0;break;case 8:copy_out_error=1;break;
  }
  struct wr_iot_driver_owner before=ad.wr_iot_driver_owner;
  assert(wr_iot_driver_uncertain_query_encode(wire,64,id));
  int result=wr_iot_driver_closed_ioctl(&ad,&iot,&rq);
  if(!fault){assert(!result&&wr_iot_driver_uncertain_decode(&out,id,wire,64));assert(out.attempt_token==2);}
  else assert(result<0);
  assert(!memcmp(&before,&ad.wr_iot_driver_owner,sizeof(before))&&!ad.wr_iot_transition_lock);
 }
 puts("PASS actual CLOSED configuration entry: original ON nonce/current receipt, partial close/MMIO/DMA/reset refusal, persistent foreign-ticket context, privilege/copy failures. No RF/FIFO/isolation-release proof.");return 0;
}
