#include <assert.h>
#include <stddef.h>
#include <string.h>
#define WDS_SUPPORT 1
#define WDEV_NUM_MAX 2
#define WR_REF_FAMILY_WDS 4
#define FALSE 0
typedef unsigned long ULONG;typedef unsigned int UINT;typedef int INT;
struct wifi_dev {void *if_dev;};
struct entry {int wds;struct wifi_dev *wdev;unsigned char Addr[6];};
struct wr_iot_interface_ref {void *device;unsigned long generation;int family,published;struct {unsigned int active,retirement_stage;} peer_operation;};
struct adapter {int MacTabLock,wr_iot_transition_lock;struct wr_iot_interface_ref wr_iot_interface_refs[3];};
static int mac,transition,mutated;
#define IS_ENTRY_WDS(e) ((e)->wds)
#define MAC_ADDR_EQUAL(a,b) (!memcmp((a),(b),6))
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(mac&&!transition);transition=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(mac&&transition);transition=0;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(mac&&!transition);mac=0;}while(0)
static int remove_peer(struct adapter *pAd,struct entry *pEntry,const unsigned char *pAddr){
#include "wds-peer-delete-gate.inc"
assert(mac&&!transition);mutated++;return 1;}
int main(void){struct adapter a={0};int dev;struct wifi_dev w={&dev};struct entry e={1,&w,{1,2,3,4,5,6}};
unsigned char addr[6]={1,2,3,4,5,6},wrong[6]={6,5,4,3,2,1};
a.wr_iot_interface_refs[0]=(struct wr_iot_interface_ref){&dev,1,WR_REF_FAMILY_WDS,1,{1,0}};
mac=1;assert(!remove_peer(&a,&e,addr)&&!mac&&!mutated);
a.wr_iot_interface_refs[0].peer_operation.active=0;
mac=1;assert(!remove_peer(&a,&e,wrong)&&!mac&&!mutated);
mac=1;assert(!remove_peer(&a,&e,NULL)&&!mac&&!mutated);
a.wr_iot_interface_refs[0].peer_operation.retirement_stage=1;
mac=1;assert(remove_peer(&a,&e,addr)&&mac&&mutated==1);
a.wr_iot_interface_refs[0].peer_operation.retirement_stage=2;mac=1;
assert(!remove_peer(&a,&e,addr)&&!mac&&mutated==1);
a.wr_iot_interface_refs[0].peer_operation.retirement_stage=3;mac=1;
assert(!remove_peer(&a,&e,addr)&&!mac&&mutated==1);
a.wr_iot_interface_refs[0].peer_operation.retirement_stage=0;
a.wr_iot_interface_refs[0].generation=0;mac=1;
assert(!remove_peer(&a,&e,addr)&&!mac&&mutated==1);
e.wds=0;mac=1;assert(remove_peer(&a,&e,NULL)&&mac&&mutated==2);
e.wds=1;e.wdev=NULL;mac=1;assert(!remove_peer(&a,&e,addr)&&!mac&&mutated==2);
return 0;}
