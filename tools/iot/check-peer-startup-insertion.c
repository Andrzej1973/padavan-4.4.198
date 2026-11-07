#include "peer-open-owner.h"
#include <assert.h>
#include <stddef.h>
#define ENTRY_WDS 2
#define WR_OTHER_ENTRY 1
typedef struct {int MacTabLock;unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_open_owner wr_iot_peer_open_owner;} ADAPTER;
static int held,body_calls;
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
static void *insert(ADAPTER *pAd,int ent_type,const struct wr_iot_peer_open_ticket *wr_open_ticket,unsigned long wr_open_lease){
 assert(!held);held=1;
#include "wr-iot-peer-startup-insertion-gate.inc"
 body_calls++;held=0;return pAd;
}
int main(void){ADAPTER a={0};struct wr_iot_peer_open_ticket t={0},bad;int device,other;unsigned long lease,old;
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);wr_iot_peer_open_owner_init(&a.wr_iot_peer_open_owner);
 assert(insert(&a,WR_OTHER_ENTRY,NULL,0)&&body_calls==1);
 assert(wr_iot_peer_open_begin(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&device,1,&t));
 assert(!insert(&a,ENTRY_WDS,NULL,0)&&!held);
 assert(!insert(&a,ENTRY_WDS,&t,1)&&!held);
 assert(wr_iot_peer_open_startup(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t));
 lease=wr_iot_peer_open_insert_begin(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t);assert(lease);
 assert(!insert(&a,WR_OTHER_ENTRY,&t,lease)&&!held);
 bad=t;bad.device=&other;assert(!insert(&a,ENTRY_WDS,&bad,lease)&&!held);
 bad=t;bad.serial++;assert(!insert(&a,ENTRY_WDS,&bad,lease)&&!held);
 assert(!insert(&a,ENTRY_WDS,NULL,lease)&&!held);
 assert(!insert(&a,ENTRY_WDS,&t,0)&&!held);
 assert(!insert(&a,ENTRY_WDS,&t,lease+1)&&!held);
 assert(insert(&a,ENTRY_WDS,&t,lease)&&body_calls==2);
 assert(!insert(&a,ENTRY_WDS,&t,lease)&&!held&&body_calls==2);
 assert(wr_iot_peer_open_insert_end(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t,lease));old=lease;
 lease=wr_iot_peer_open_insert_begin(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t);
 assert(!insert(&a,ENTRY_WDS,&t,old)&&!held);
 assert(wr_iot_peer_open_finish(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t,0));
 assert(!insert(&a,ENTRY_WDS,&t,lease)&&!held&&body_calls==2);
 return 0;
}
