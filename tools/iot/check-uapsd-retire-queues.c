#include <assert.h>
#include <stddef.h>
#define WMM_NUM_OF_AC 4
#define MAX_LEN_OF_TR_TABLE 3
#define NDIS_STATUS_FAILURE -1
#define NDIS_STATUS_SUCCESS 0
#define READ_ONCE(x) (x)
typedef int INT;typedef unsigned int UINT32;typedef unsigned long ULONG;
typedef struct packet {struct packet *next;int id;} QUEUE_ENTRY,*PQUEUE_ENTRY;
typedef struct {QUEUE_ENTRY *Head,*Tail;unsigned int Number;} QUEUE_HEADER;
typedef struct {unsigned int wcid;QUEUE_HEADER UAPSDQueue[4];PQUEUE_ENTRY pUAPSDEOSPFrame;int UAPSDTxNum,bAPSDFlagSPStart,bAPSDFlagEOSPOK;} MAC_TABLE_ENTRY;
typedef struct {int UAPSDEOSPLock;struct {struct {int enq_cap,deq_cap;} tr_entry[3];} MacTab;} RTMP_ADAPTER;
static int held,released[8],joins;
#define UAPSD_SEM_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;joins++;}while(0)
#define UAPSD_SEM_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define InitializeQueueHeader(q) do{assert(held);*(q)=(QUEUE_HEADER){0};}while(0)
#define QUEUE_ENTRY_TO_PACKET(e) (e)
#define RELEASE_NDIS_PACKET(a,p,s) do{(void)(a);(void)(s);assert(!held);assert((p)->id<8);assert(!released[(p)->id]);released[(p)->id]++;}while(0)
static void RtmpCleanupPsQueue(RTMP_ADAPTER *a,QUEUE_HEADER *q){
 while(q->Head){PQUEUE_ENTRY e=q->Head;q->Head=e->next;RELEASE_NDIS_PACKET(a,e,-1);}q->Number=0;
}
#include "uapsd-retire-queues.inc"
int main(void){RTMP_ADAPTER a={0};MAC_TABLE_ENTRY e={0};QUEUE_ENTRY packets[5];unsigned int i;
e.wcid=1;for(i=0;i<4;i++){packets[i]=(QUEUE_ENTRY){NULL,(int)i};e.UAPSDQueue[i]=(QUEUE_HEADER){&packets[i],&packets[i],1};}
packets[4]=(QUEUE_ENTRY){NULL,4};e.pUAPSDEOSPFrame=&packets[4];e.UAPSDTxNum=e.bAPSDFlagSPStart=e.bAPSDFlagEOSPOK=1;
a.MacTab.tr_entry[1].enq_cap=1;assert(wr_iot_uapsd_retire_queues(&a,&e)==-1);assert(e.UAPSDQueue[0].Number==1&&!released[0]&&!held);
a.MacTab.tr_entry[1].enq_cap=0;a.MacTab.tr_entry[1].deq_cap=1;assert(wr_iot_uapsd_retire_queues(&a,&e)==-1);
a.MacTab.tr_entry[1].deq_cap=0;assert(wr_iot_uapsd_retire_queues(&a,&e)==0);
for(i=0;i<5;i++){assert(released[i]==1);}
for(i=0;i<4;i++){assert(!e.UAPSDQueue[i].Head&&!e.UAPSDQueue[i].Number);}
assert(!e.pUAPSDEOSPFrame&&!e.UAPSDTxNum&&!e.bAPSDFlagSPStart&&!e.bAPSDFlagEOSPOK&&!held);
assert(wr_iot_uapsd_retire_queues(&a,&e)==0);for(i=0;i<5;i++)assert(released[i]==1);
e.wcid=3;i=(unsigned int)joins;assert(wr_iot_uapsd_retire_queues(&a,&e)==-1);assert((unsigned int)joins==i);assert(wr_iot_uapsd_retire_queues(&a,NULL)==-1);return 0;}
