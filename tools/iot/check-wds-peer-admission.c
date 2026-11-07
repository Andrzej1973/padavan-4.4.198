#include <assert.h>
#include <stddef.h>
#define MAX_LEN_OF_MAC_TABLE 5
#define MAX_LEN_OF_TR_TABLE 4
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_SUCCESS 0
#define FALSE 0
typedef int INT;typedef unsigned int UINT;typedef unsigned long ULONG;
struct wifi_dev {int id;};
typedef struct {struct wifi_dev *wdev;unsigned int wcid;int type;} MAC_TABLE_ENTRY;
typedef struct {int MacTabLock,irq_lock;struct {MAC_TABLE_ENTRY Content[5];struct {int enq_cap,deq_cap;} tr_entry[4];} MacTab;} RTMP_ADAPTER;
static int mac,irq,writes;
#define IS_ENTRY_NONE(e) ((e)->type==0)
#define IS_ENTRY_WDS(e) ((e)->type==2)
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!mac&&!irq);mac=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(mac&&!irq);mac=0;}while(0)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(mac&&!irq);irq=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(mac&&irq);irq=0;}while(0)
#define WRITE_ONCE(x,v) do{assert(mac&&irq);(x)=(v);writes++;}while(0)
#include "wds-peer-admission.inc"
int main(void){RTMP_ADAPTER a={0};struct wifi_dev w={0},other={1};
for(int i=0;i<4;i++){a.MacTab.tr_entry[i].enq_cap=a.MacTab.tr_entry[i].deq_cap=1;}
a.MacTab.Content[1]=(MAC_TABLE_ENTRY){&w,1,2};
a.MacTab.Content[2]=(MAC_TABLE_ENTRY){&other,2,1};
assert(wr_iot_wds_block_peer_admission(&a,&w)==0&&writes==2&&!mac&&!irq);
assert(!a.MacTab.tr_entry[1].enq_cap&&a.MacTab.tr_entry[2].enq_cap&&a.MacTab.tr_entry[0].enq_cap);
a.MacTab.Content[3]=(MAC_TABLE_ENTRY){&w,3,1};writes=0;
assert(wr_iot_wds_block_peer_admission(&a,&w)==-1&&!writes&&!mac&&!irq);
a.MacTab.Content[3]=(MAC_TABLE_ENTRY){0};a.MacTab.Content[1].wcid=2;
assert(wr_iot_wds_block_peer_admission(&a,&w)==-1&&!writes);
a.MacTab.Content[1].wcid=1;a.MacTab.Content[4]=(MAC_TABLE_ENTRY){&w,4,2};
assert(wr_iot_wds_block_peer_admission(&a,&w)==-1&&!writes);
assert(wr_iot_wds_block_peer_admission(NULL,&w)==-1);return 0;}
