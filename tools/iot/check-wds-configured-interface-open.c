#include <assert.h>
#include <stddef.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define MAX_WDS_ENTRY 2
#define WDEV_NUM_MAX 2
#define WR_REF_FAMILY_WDS 3
#define WR_REF_OWNED 2
typedef int BOOLEAN;typedef unsigned int UINT;typedef unsigned long ULONG;
typedef unsigned char UCHAR;typedef void *PNET_DEV;
struct wr_iot_peer_open_ticket;
typedef struct {int value;} MAC_TABLE_ENTRY;
struct wr_iot_interface_ref {void *device;unsigned long generation;int published,removing,family,phase;};
typedef struct {int wr_iot_transition_lock;
 struct {int retiring,pm_suspending,pm_suspended;} wr_iot_transition;
 struct {struct {struct {void *if_dev;} wdev;int Valid;UCHAR PeerWdsAddr[6];} WdsEntry[2];} WdsTab;
 struct wr_iot_interface_ref wr_iot_interface_refs[3];} RTMP_ADAPTER;
static int held,calls,fail_lower,change_generation;static MAC_TABLE_ENTRY peer;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static struct wr_iot_interface_ref *wr_iot_registry_find(struct wr_iot_interface_ref *r,UINT n,void *dev,unsigned long generation){
 assert(held);for(UINT i=0;i<n;i++)if(r[i].device==dev&&r[i].generation==generation)return &r[i];return NULL;}
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_identity(RTMP_ADAPTER *a,UCHAR *addr,UINT index,UINT mode,
 const struct wr_iot_peer_open_ticket *ticket,unsigned long lease,PNET_DEV dev,unsigned long generation){
 assert(!held&&index==0&&mode==2&&!ticket&&!lease);assert(addr==a->WdsTab.WdsEntry[0].PeerWdsAddr);calls++;
 if(change_generation)a->wr_iot_interface_refs[0].generation++;
 if(fail_lower||a->wr_iot_interface_refs[0].device!=dev||a->wr_iot_interface_refs[0].generation!=generation)return NULL;
 return &peer;
}
#include "wr-iot-wds-configured-interface-open.inc"
static RTMP_ADAPTER a;static int device,other;
static void setup(void){memset(&a,0,sizeof a);held=calls=fail_lower=change_generation=0;
 a.WdsTab.WdsEntry[0].wdev.if_dev=&device;
 a.wr_iot_interface_refs[0]=(struct wr_iot_interface_ref){&device,7,1,0,WR_REF_FAMILY_WDS,WR_REF_OWNED};}
int main(void){setup();assert(!wr_iot_wds_configured_interface_open(NULL,&device,7));
 assert(!wr_iot_wds_configured_interface_open(&a,NULL,7));assert(!wr_iot_wds_configured_interface_open(&a,&device,0));
 assert(!wr_iot_wds_configured_interface_open(&a,&other,7)&&!calls&&!held);
 assert(!wr_iot_wds_configured_interface_open(&a,&device,8)&&!calls&&!held);
 assert(wr_iot_wds_configured_interface_open(&a,&device,7)&&!calls&&!held);
 a.WdsTab.WdsEntry[0].Valid=1;assert(wr_iot_wds_configured_interface_open(&a,&device,7)&&calls==1&&!held);
 fail_lower=1;assert(!wr_iot_wds_configured_interface_open(&a,&device,7)&&calls==2&&!held);
 setup();a.wr_iot_interface_refs[0].phase=0;assert(!wr_iot_wds_configured_interface_open(&a,&device,7)&&!calls&&!held);
 setup();a.wr_iot_interface_refs[0].removing=1;assert(!wr_iot_wds_configured_interface_open(&a,&device,7)&&!calls&&!held);
 setup();a.wr_iot_interface_refs[0].published=0;assert(!wr_iot_wds_configured_interface_open(&a,&device,7)&&!calls&&!held);
 setup();a.wr_iot_transition.pm_suspending=1;assert(!wr_iot_wds_configured_interface_open(&a,&device,7)&&!calls&&!held);
 setup();a.wr_iot_transition.retiring=1;assert(!wr_iot_wds_configured_interface_open(&a,&device,7)&&!calls&&!held);
 setup();a.WdsTab.WdsEntry[0].Valid=1;change_generation=1;
 assert(!wr_iot_wds_configured_interface_open(&a,&device,7)&&calls==1&&!held);
 return 0;}
