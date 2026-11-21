#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
#include "precreated-idle-probe.h"
#include "precreated-idle-wire.h"
typedef int INT;typedef unsigned long ULONG;typedef void *PNET_DEV;
#define WDEV_NUM_MAX 1
struct ifreq {void *ifr_data;};
typedef struct adapter {
 int mt7603,wr_iot_transition_lock,wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed;
 struct {int active,poisoned;} wr_iot_driver_owner;
 struct {int active;} wr_iot_close_owner;
 struct {int BssidNum;struct {struct {PNET_DEV if_dev;} wdev;} MBSSID[3];} ApCfg;
 PNET_DEV net_dev;struct wr_iot_interface_ref wr_iot_interface_refs[2];
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_precreated_idle_probe wr_iot_idle_probe;
} *PRTMP_ADAPTER;
#define IS_MT7603(ad) ((ad)->mt7603)
#define VIRTUAL_IF_NUM(ad) 1
#define RTMP_IRQ_LOCK(lock,flags) do{assert(!*(lock));*(lock)=1;(flags)=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{assert(*(lock)&&(flags));*(lock)=0;}while(0)
static int fault,probes,copies;static PRTMP_ADAPTER tested_adapter;
static INT wr_iot_precreated_idle_probe_driver(PRTMP_ADAPTER ad,PNET_DEV dev,struct wr_iot_precreated_idle_probe *p,unsigned long generation){
 assert(!ad->wr_iot_transition_lock);probes++;
 if(fault==1)return -EUCLEAN;
 assert(wr_iot_precreated_idle_probe_begin(p,&ad->wr_iot_transition,ad->wr_iot_interface_refs,2,ad->net_dev,dev,generation,1));
 assert(wr_iot_precreated_idle_probe_finish(p,&ad->wr_iot_transition,ad->wr_iot_interface_refs,2,1,1));
 if(fault==2)p->accepted=0;
 if(fault==3)ad->wr_iot_transition.serial++;
 if(fault==4)ad->wr_iot_close_owner.active=1;
 if(fault==5)ad->wr_iot_control_users=1;
 return 0;
}
static int copy_to_user(void *out,const void *in,unsigned n){copies++;assert(n==64&&!tested_adapter->wr_iot_transition_lock);if(fault==6)return 1;memcpy(out,in,n);return 0;}
#include "precreated-idle-entry.inc"
int main(void){
 for(fault=0;fault<9;fault++){
  int main_dev,iot_dev;struct adapter ad={.mt7603=1,.net_dev=&main_dev,.ApCfg.BssidNum=3};
  tested_adapter=&ad;ad.ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  unsigned long seq=0;struct wr_iot_interface_ref *main=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&seq,&main_dev,WR_REF_FAMILY_MAIN);
  struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(ad.wr_iot_interface_refs,2,&seq,&iot_dev,WR_REF_FAMILY_MBSS);
  main->published=iot->published=1;main->phase=WR_REF_OWNED;main->last_token=1;
  unsigned char nonce[16]={1},wire[64],reply[64]={0};assert(wr_iot_idle_query_encode(wire,64,nonce));struct ifreq rq={reply};
  if(fault==7)wire[63]=1;
  if(fault==8)iot->published=0;
  probes=copies=0;int result=wr_iot_precreated_idle_reply(&ad,&iot_dev,&rq,wire);
  assert((result==0)==(fault==0));assert(!ad.wr_iot_transition_lock);
  assert(copies==(fault==0||fault==6));
  if(fault>=7)assert(!probes);
  if(!fault){struct wr_iot_idle_result out;assert(wr_iot_idle_reply_decode(&out,nonce,reply,64)&&out.generation==2&&out.serial);}
 }
 puts("PASS actual idle endpoint reply: failed probe, unaccepted/changed serial, CLOSE/control conflicts, copy fault and strict query; persistent probe executor injected, common privilege route pending");
 return 0;
}
