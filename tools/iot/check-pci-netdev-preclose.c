#include "interface-registry.h"
#include "aux-family-close.h"
#include <assert.h>
#define WDEV_NUM_MAX 3
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_SUCCESS 0
typedef unsigned long ULONG;
typedef void *PNET_DEV;
typedef struct {
 int wr_iot_transition_lock;
 struct {int retiring;} wr_iot_transition;
 unsigned int wr_iot_registration_inflight;
 struct wr_iot_interface_ref wr_iot_interface_refs[4];
 struct wr_iot_family_close wr_iot_family_close[4];
} RTMP_ADAPTER;
static int locked,protected,calls,fail_slot=-1,mutate_slot=-1,root_mutates_child;
static RTMP_ADAPTER *active;
static void *order[4];
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(locked);locked=0;}while(0)
static void RtmpOSNetDevProtect(int on){assert(!locked&&protected!=on);protected=on;}
static void RtmpOSNetDevClose(void *device){
 unsigned int i;assert(protected&&!locked);order[calls++]=device;
 for(i=0;i<4;i++)if(active->wr_iot_interface_refs[i].device==device){
  struct wr_iot_interface_ref *r=&active->wr_iot_interface_refs[i];
  if((int)i==fail_slot){r->phase=WR_REF_CLOSING;return;}
  r->phase=WR_REF_IDLE;r->close_stage=r->family==WR_REF_FAMILY_WDS?2:4;
  if((int)i==mutate_slot)r->generation++;
  if(i==0&&root_mutates_child)active->wr_iot_interface_refs[1].generation++;
  return;
 }
 assert(0);
}
#include "pci-netdev-preclose.inc"
static void ready(RTMP_ADAPTER *a,int *dev){
 unsigned int i;*a=(RTMP_ADAPTER){0};a->wr_iot_transition.retiring=1;
 for(i=0;i<4;i++)wr_iot_ref_init(&a->wr_iot_interface_refs[i],0,0);
 for(i=0;i<3;i++){
  struct wr_iot_interface_ref *r=&a->wr_iot_interface_refs[i];
  wr_iot_ref_init(r,&dev[i],i+1);r->published=1;r->last_token=1;r->phase=WR_REF_OWNED;
  r->family=i==0?WR_REF_FAMILY_MAIN:i==1?WR_REF_FAMILY_WDS:WR_REF_FAMILY_MBSS;
 }
 active=a;calls=0;fail_slot=mutate_slot=-1;root_mutates_child=0;
}
int main(void){RTMP_ADAPTER a;int dev[4];
 ready(&a,dev);assert(wr_iot_pci_netdev_preclose(&a,&dev[0])==0);
 assert(calls==3&&order[0]==&dev[1]&&order[1]==&dev[2]&&order[2]==&dev[0]);
 for(unsigned i=0;i<3;i++)assert(a.wr_iot_interface_refs[i].device==&dev[i]&&a.wr_iot_interface_refs[i].published&&!a.wr_iot_interface_refs[i].removing);
 assert(!protected&&!locked);calls=0;assert(!wr_iot_pci_netdev_preclose(&a,&dev[0])&&!calls);
 ready(&a,dev);fail_slot=1;assert(wr_iot_pci_netdev_preclose(&a,&dev[0])==-1&&calls==1&&!protected&&!locked);
 assert(a.wr_iot_interface_refs[0].phase==WR_REF_OWNED);
 ready(&a,dev);mutate_slot=1;assert(wr_iot_pci_netdev_preclose(&a,&dev[0])==-1&&calls==1);
 ready(&a,dev);root_mutates_child=1;assert(wr_iot_pci_netdev_preclose(&a,&dev[0])==-1&&calls==3);
 ready(&a,dev);a.wr_iot_registration_inflight=1;assert(wr_iot_pci_netdev_preclose(&a,&dev[0])==-1&&!calls);
 ready(&a,dev);a.wr_iot_transition.retiring=0;assert(wr_iot_pci_netdev_preclose(&a,&dev[0])==-1&&!calls);
 ready(&a,dev);a.wr_iot_interface_refs[2].family=WR_REF_FAMILY_UNKNOWN;assert(wr_iot_pci_netdev_preclose(&a,&dev[0])==-1&&!calls);
 return 0;
}
