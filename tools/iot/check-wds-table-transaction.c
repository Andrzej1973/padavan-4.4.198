#include "peer-open-owner.h"
#include "peer-close-executor.h"
#include <assert.h>
#include <stddef.h>
#define MAX_WDS_ENTRY 2
#define FALSE 0
typedef int BOOLEAN;typedef unsigned int UINT;typedef unsigned char UCHAR;typedef void *PNET_DEV;
typedef struct {int value;} MAC_TABLE_ENTRY;
typedef struct {int MacTabLock;unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;} RTMP_ADAPTER;
static int held,calls,fail_body,nest;static MAC_TABLE_ENTRY peer;
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
static int delete_attempt(RTMP_ADAPTER *pAd){unsigned long wr_table_serial=0;held=1;
#include "wr-iot-peer-table-delete-gate.inc"
 held=0;return 1;
}
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_identity_body(RTMP_ADAPTER *,UCHAR *,UINT,UINT,
 const struct wr_iot_peer_open_ticket *,unsigned long,PNET_DEV,unsigned long);
#include "wr-iot-wds-table-transaction.inc"
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_identity_body(RTMP_ADAPTER *a,UCHAR *addr,UINT index,UINT mode,
 const struct wr_iot_peer_open_ticket *ticket,unsigned long lease,PNET_DEV device,unsigned long generation){
 (void)index;(void)mode;(void)lease;(void)device;(void)generation;
 assert(!held);calls++;
 if(!ticket){
  assert(a->wr_iot_peer_table_owner.transactions);
  held=1;assert(!wr_iot_peer_table_begin(&a->wr_iot_peer_table_owner));held=0;
  assert(!delete_attempt(a)&&!held);
  if(nest){nest=0;assert(wr_iot_wds_insert_transaction_identity(a,addr,1,0,NULL,0,NULL,0)==&peer);}
 }
 return fail_body?NULL:&peer;
}
int main(void){RTMP_ADAPTER a={0};UCHAR addr[6]={0};unsigned long serial;struct wr_iot_peer_open_ticket ticket={&a,1};
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);nest=1;
 assert(wr_iot_wds_insert_transaction_identity(&a,addr,0,2,NULL,0,NULL,0)==&peer);
 assert(calls==2&&!a.wr_iot_peer_table_owner.transactions&&!held&&delete_attempt(&a));
 fail_body=1;assert(!wr_iot_wds_insert_transaction_identity(&a,addr,0,2,NULL,0,NULL,0));
 assert(!a.wr_iot_peer_table_owner.transactions&&!held);fail_body=0;
 serial=wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner);assert(serial);
 {int before=calls;assert(!wr_iot_wds_insert_transaction_identity(&a,addr,0,2,NULL,0,NULL,0)&&calls==before&&!held);}
 assert(wr_iot_peer_table_finish(&a.wr_iot_peer_table_owner,serial,1));
 assert(!wr_iot_wds_insert_transaction_identity(&a,addr,0,2,NULL,1,NULL,0));
 assert(!wr_iot_wds_insert_transaction_identity(&a,addr,0,2,&ticket,0,NULL,0));
 assert(wr_iot_wds_insert_transaction_identity(&a,addr,0,2,&ticket,1,NULL,0)==&peer);
 assert(!a.wr_iot_peer_table_owner.transactions&&!held);
#ifdef WR_IOT_WDS_EXECUTOR_GUARD
 {int before=calls;
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_RESET,0));
 assert(!wr_iot_wds_insert_transaction_identity(&a,addr,0,2,NULL,0,NULL,0)&&calls==before);
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_RESET,0,1,1));
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,8));
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,8,0,1));
 assert(!wr_iot_wds_insert_transaction_identity(&a,addr,0,2,NULL,0,NULL,0)&&calls==before);
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,8));
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_CHECKED,8,1,1));
 }
#endif
 a.wr_iot_peer_table_owner.transactions=~0U;
 assert(!wr_iot_wds_insert_transaction_identity(&a,addr,0,2,NULL,0,NULL,0)&&a.wr_iot_peer_table_owner.poisoned);
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);
 assert(!wr_iot_peer_table_transaction_leave(&a.wr_iot_peer_table_owner)&&a.wr_iot_peer_table_owner.poisoned);
 return 0;
}
