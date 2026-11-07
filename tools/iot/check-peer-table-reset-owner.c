/* Actual reservation/gate fragments, injected lock and table layouts. */
#include "peer-table-owner.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
typedef int BOOLEAN;typedef unsigned int UINT;
struct wifi_dev {int id;};
typedef struct {struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
typedef struct {int wr_iot_setup_observed,wr_iot_setup_result;} STA_TR_ENTRY;
typedef struct {int MacTabLock;unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct {MAC_TABLE_ENTRY Content[4];STA_TR_ENTRY tr_entry[3];} MacTab;} RTMP_ADAPTER;
static int held;
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#include "wr-iot-peer-table-reset-owner.inc"
static void *insert(RTMP_ADAPTER *pAd){
 NdisAcquireSpinLock(&pAd->MacTabLock);
#include "wr-iot-peer-table-insertion-gate.inc"
 NdisReleaseSpinLock(&pAd->MacTabLock);return pAd;
}
static int deletion(RTMP_ADAPTER *pAd,unsigned long wr_table_serial){
 NdisAcquireSpinLock(&pAd->MacTabLock);
#include "wr-iot-peer-table-delete-gate.inc"
 NdisReleaseSpinLock(&pAd->MacTabLock);return TRUE;
}
int main(void){RTMP_ADAPTER a={0};struct wifi_dev one={1},two={2};unsigned long t,next;
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);
 a.MacTab.Content[1].wdev=&one;a.MacTab.tr_entry[1]=(STA_TR_ENTRY){1,-2};
 assert(!wr_iot_peer_reset_begin(&a,NULL)&&!held&&insert(&a));
 assert(!wr_iot_peer_reset_begin(&a,&one)&&!held);
 t=wr_iot_peer_reset_begin(&a,&two);assert(t&&!held);
 assert(!insert(&a)&&!held&&!deletion(&a,0)&&!held);
 assert(!deletion(&a,t+1)&&!held&&deletion(&a,t)&&!held);
 assert(!wr_iot_peer_reset_begin(&a,&two)&&!held);
 assert(wr_iot_peer_reset_finish(&a,t,TRUE)&&!held&&insert(&a));
 a.MacTab.tr_entry[1].wr_iot_setup_result=0;
 next=wr_iot_peer_reset_begin(&a,NULL);assert(next>t&&!held);
 /* Full MacTab clear must not erase the adapter-owned reservation. */
 memset(&a.MacTab,0,sizeof a.MacTab);assert(!insert(&a)&&!held);
 assert(!wr_iot_peer_reset_finish(&a,t,TRUE)&&!held);
 assert(!wr_iot_peer_reset_finish(&a,next,FALSE)&&!held);
 assert(!insert(&a)&&!held&&!deletion(&a,next)&&!held);
 assert(!wr_iot_peer_reset_begin(&a,NULL)&&!held);
 return 0;
}
