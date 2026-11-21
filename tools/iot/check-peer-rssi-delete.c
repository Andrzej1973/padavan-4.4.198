/* Compile against the actual merged include directory. Vendor deletion is
 * injected: this tests admission/context transport, not callback retirement. */
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#include "peer-table-owner.h"
#include "peer-close-executor.h"
typedef int BOOLEAN;
typedef unsigned short USHORT;
typedef unsigned char UCHAR;
#define FALSE 0
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 4
struct wr_rssi_identity { int value; };
struct wr_rssi_record { int value; };
typedef struct {
 int MacTabLock;
 unsigned int wr_iot_peer_delete_active;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
} RTMP_ADAPTER;
static int held,calls,result=1,reenter;
static const void *expected_device;
static unsigned long expected_generation,expected_resume,expected_table;
static const struct wr_rssi_identity *expected_identity;
static const struct wr_rssi_record *expected_attempt;
#define NdisAcquireSpinLock(lock) ((void)(lock),assert(!held),held=1)
#define NdisReleaseSpinLock(lock) ((void)(lock),assert(held),held=0)
BOOLEAN wr_rssi_delete_entry(RTMP_ADAPTER *,USHORT,UCHAR *,
 const struct wr_rssi_identity *,const struct wr_rssi_record *);
static BOOLEAN wr_iot_mac_delete_entry_body(RTMP_ADAPTER *ad,USHORT wcid,UCHAR *mac,
 const void *device,unsigned long generation,unsigned long resume,unsigned long table,
 const struct wr_rssi_identity *identity,const struct wr_rssi_record *attempt)
{
 assert(!held&&ad&&wcid<4&&mac);
 assert(table?wr_iot_peer_table_allows(&ad->wr_iot_peer_table_owner,table):
        ad->wr_iot_peer_delete_active==1);
 assert(device==expected_device&&generation==expected_generation);
 assert(resume==expected_resume&&table==expected_table);
 assert(identity==expected_identity&&attempt==expected_attempt);
 calls++;
 if(reenter){
  int before=calls;reenter=0;
  assert(!wr_rssi_delete_entry(ad,wcid,mac,identity,attempt));
  assert(calls==before);
 }
 return result;
}
#include "wr-iot-peer-normal-delete.inc"

int main(void)
{
 RTMP_ADAPTER ad={0};UCHAR mac[6]={0};
 struct wr_rssi_identity identity={7};struct wr_rssi_record attempt={9};
 unsigned long table;int before;
 expected_identity=&identity;expected_attempt=&attempt;reenter=1;
 assert(wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 assert(calls==1&&!ad.wr_iot_peer_delete_active&&!held);
 result=0;assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 assert(calls==2&&!ad.wr_iot_peer_delete_active&&!held);
 result=1;assert(wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 before=calls;
 ad.wr_iot_peer_delete_active=1;
 assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 assert(ad.wr_iot_peer_delete_active==1);ad.wr_iot_peer_delete_active=0;
 ad.wr_iot_peer_table_owner.transactions=1;
 assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 ad.wr_iot_peer_table_owner.transactions=0;
 ad.wr_iot_peer_close_executor.lane=WR_PEER_CLOSE_CHECKED;
 assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 wr_iot_peer_close_executor_init(&ad.wr_iot_peer_close_executor);
 ad.wr_iot_peer_table_owner.closed=1;
 assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 ad.wr_iot_peer_table_owner.closed=0;
 ad.wr_iot_peer_table_owner.retained=1;
 assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 ad.wr_iot_peer_table_owner.retained=0;
 ad.wr_iot_peer_table_owner.poisoned=1;
 assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 ad.wr_iot_peer_table_owner.poisoned=0;
 assert(!wr_rssi_delete_entry(NULL,1,mac,&identity,&attempt));
 assert(!wr_rssi_delete_entry(&ad,4,mac,&identity,&attempt));
 assert(!wr_rssi_delete_entry(&ad,1,NULL,&identity,&attempt));
 assert(calls==before&&!held);

 expected_identity=NULL;expected_attempt=NULL;
 expected_device=&identity;expected_generation=23;expected_resume=29;
 assert(wr_iot_mac_delete_entry(&ad,1,mac,&identity,23,29,0));
 table=wr_iot_peer_table_begin(&ad.wr_iot_peer_table_owner);assert(table);
 before=calls;
 assert(!wr_rssi_delete_entry(&ad,1,mac,&identity,&attempt));
 assert(!wr_iot_mac_delete_entry(&ad,1,mac,&identity,23,29,table+1));
 assert(calls==before);
 expected_table=table;
 assert(wr_iot_mac_delete_entry(&ad,1,mac,&identity,23,29,table));
 assert(ad.wr_iot_peer_table_owner.active&&!ad.wr_iot_peer_delete_active);
 assert(wr_iot_peer_table_finish(&ad.wr_iot_peer_table_owner,table,1));
 assert(!held);
 puts("PASS merged RSSI/IoT deletion admission, reentry refusal, failed-body lease release and WDS/reset context transport; vendor body injected");
 return 0;
}
