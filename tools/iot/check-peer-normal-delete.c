#include "peer-table-owner.h"
#include "peer-close-executor.h"
#include <assert.h>
#include <stddef.h>
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
#define FALSE 0
typedef int BOOLEAN;typedef unsigned short USHORT;typedef unsigned char UCHAR;
typedef struct {int MacTabLock;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;} RTMP_ADAPTER;
static int held,calls,fail;static unsigned long observed;
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
static BOOLEAN wr_iot_mac_delete_entry_body(RTMP_ADAPTER *a,USHORT w,UCHAR *addr,
 const void *device,unsigned long generation,unsigned long resume,unsigned long serial){
 (void)w;(void)addr;(void)device;(void)generation;(void)resume;
 assert(!held&&serial);calls++;observed=serial;
 NdisAcquireSpinLock(&a->MacTabLock);
 assert(wr_iot_peer_table_allows(&a->wr_iot_peer_table_owner,serial));
 assert(!wr_iot_peer_table_begin(&a->wr_iot_peer_table_owner));
 assert(!wr_iot_peer_table_transaction_enter(&a->wr_iot_peer_table_owner));
 NdisReleaseSpinLock(&a->MacTabLock);
 return !fail;
}
#include "wr-iot-peer-normal-delete.inc"
int main(void){RTMP_ADAPTER a={0};UCHAR addr[6]={0};unsigned long serial;
 assert(wr_iot_mac_delete_entry(&a,1,addr,NULL,0,0,0)&&calls==1&&observed);
 assert(!a.wr_iot_peer_table_owner.active);
 assert(wr_iot_peer_table_transaction_enter(&a.wr_iot_peer_table_owner));
 assert(!wr_iot_mac_delete_entry(&a,1,addr,NULL,0,0,0)&&calls==1);
 assert(wr_iot_peer_table_transaction_leave(&a.wr_iot_peer_table_owner));
 serial=wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner);assert(serial);
 assert(!wr_iot_mac_delete_entry(&a,1,addr,NULL,0,0,serial+1)&&calls==1);
 assert(wr_iot_mac_delete_entry(&a,1,addr,NULL,0,0,serial)&&observed==serial);
 assert(a.wr_iot_peer_table_owner.active); /* Parent reset still owns it. */
 assert(wr_iot_peer_table_finish(&a.wr_iot_peer_table_owner,serial,1));
 assert(!wr_iot_mac_delete_entry(&a,3,addr,NULL,0,0,0)&&calls==2);
 fail=1;assert(!wr_iot_mac_delete_entry(&a,1,addr,NULL,0,0,0));
 assert(a.wr_iot_peer_table_owner.retained&&a.wr_iot_peer_table_owner.active);
 assert(!wr_iot_mac_delete_entry(&a,1,addr,NULL,0,0,0)&&calls==3&&!held);
 return 0;
}
