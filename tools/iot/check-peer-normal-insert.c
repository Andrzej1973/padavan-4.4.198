#include "peer-table-owner.h"
#include "peer-close-executor.h"
#include <assert.h>
#include <stddef.h>
typedef int BOOLEAN;typedef unsigned char UCHAR;typedef unsigned int UINT32;
struct wifi_dev {int id;};typedef struct {int id;} MAC_TABLE_ENTRY;
typedef struct {int MacTabLock;unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;} RTMP_ADAPTER;
static int held,calls,fail,nested;static MAC_TABLE_ENTRY peer;
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(RTMP_ADAPTER *,UCHAR *,struct wifi_dev *,UINT32,UCHAR,BOOLEAN,const void *,unsigned long);
#include "wr-iot-peer-normal-insert.inc"
static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(RTMP_ADAPTER *a,UCHAR *addr,struct wifi_dev *w,
 UINT32 type,UCHAR mode,BOOLEAN clean,const void *ticket,unsigned long lease){
 assert(!held&&!ticket&&!lease&&a->wr_iot_peer_table_owner.transactions);calls++;
 NdisAcquireSpinLock(&a->MacTabLock);
 assert(!wr_iot_peer_table_begin(&a->wr_iot_peer_table_owner));
 NdisReleaseSpinLock(&a->MacTabLock);
 if(nested){nested=0;assert(MacTableInsertEntry(a,addr,w,type,mode,clean)==&peer);}
 /* Model the finishing tail after the vendor lock has been released. */
 assert(!held&&a->wr_iot_peer_table_owner.transactions);
 return fail?NULL:&peer;
}
int main(void){RTMP_ADAPTER a={0};UCHAR addr[6]={0};struct wifi_dev w={0};unsigned long serial;
 nested=1;assert(MacTableInsertEntry(&a,addr,&w,0,0,0)==&peer&&calls==2);
 assert(!a.wr_iot_peer_table_owner.transactions&&!held);
 fail=1;assert(!MacTableInsertEntry(&a,addr,&w,0,0,0)&&!a.wr_iot_peer_table_owner.transactions);fail=0;
 serial=wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner);assert(serial);
 assert(!MacTableInsertEntry(&a,addr,&w,0,0,0)&&calls==3);
 assert(wr_iot_peer_table_finish(&a.wr_iot_peer_table_owner,serial,1));
 assert(wr_iot_peer_close_executor_enter(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_RESET,0));
 assert(!MacTableInsertEntry(&a,addr,&w,0,0,0)&&calls==3);
 assert(wr_iot_peer_close_executor_leave(&a.wr_iot_peer_close_executor,WR_PEER_CLOSE_RESET,0,1,1));
 assert(!MacTableInsertEntry(&a,addr,NULL,0,0,0)&&calls==3);
 return 0;
}
