#include "pci-retirement-owner.h"
#include <assert.h>
#include <string.h>
#define WDEV_NUM_MAX 5
typedef unsigned long ULONG;typedef unsigned int UINT;
typedef struct {int wr_iot_transition_lock;struct wr_iot_radio_transition wr_iot_transition;
 unsigned int wr_iot_registration_inflight;struct wr_iot_pci_retirement wr_iot_pci_retirement;
 struct wr_child_teardown wr_iot_children;struct wr_iot_interface_ref wr_iot_interface_refs[6];} RTMP_ADAPTER;
static int held;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#include "wr-iot-pci-child-snapshot.inc"
static void ready(RTMP_ADAPTER *a){memset(a,0,sizeof *a);a->wr_iot_transition.retiring=1;
 a->wr_iot_pci_retirement.phase=WR_PCI_RETIRE_WORK_JOINED;}
int main(void){RTMP_ADAPTER a;int devices[6];
 ready(&a);a.wr_iot_registration_inflight=1;assert(!wr_iot_pci_children_begin(&a)&&a.wr_iot_children.phase==WR_CHILD_IDLE);
 ready(&a);a.wr_iot_transition.retiring=0;assert(!wr_iot_pci_children_begin(&a));
 ready(&a);a.wr_iot_pci_retirement.phase=WR_PCI_RETIRE_STOP_REQUESTED;assert(!wr_iot_pci_children_begin(&a));
 ready(&a);wr_iot_ref_init(&a.wr_iot_interface_refs[0],&devices[0],1);
 assert(!wr_iot_pci_children_begin(&a));
 a.wr_iot_interface_refs[0].published=1;assert(!wr_iot_pci_children_begin(&a));
 a.wr_iot_interface_refs[0].family=WR_REF_FAMILY_MAIN;
 assert(wr_iot_pci_children_begin(&a)&&a.wr_iot_children.phase==WR_CHILD_DONE&&!a.wr_iot_children.expected);
 ready(&a);
 for(unsigned int i=0;i<6;i++){
  struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[i];wr_iot_ref_init(r,&devices[i],i+1);
  r->published=1;r->family=i<5?(enum wr_iot_ref_family)(WR_REF_FAMILY_MAIN+i):WR_REF_FAMILY_MBSS;
 }
 assert(wr_iot_pci_children_begin(&a)&&a.wr_iot_children.expected==WR_CHILD_ALL);
 assert(a.wr_iot_children.phase==WR_CHILD_DRAINING&&!a.wr_iot_children.closed&&!a.wr_iot_children.completed);
 assert(!wr_iot_pci_children_begin(&a));
 ready(&a);a.wr_iot_interface_refs[0].published=1;assert(!wr_iot_pci_children_begin(&a));
 assert(!held);return 0;
}
