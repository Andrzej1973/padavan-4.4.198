#include "peer-open-owner.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define MAX_WDS_ENTRY 2
typedef int BOOLEAN;typedef unsigned int UINT;typedef unsigned char UCHAR;
typedef struct {int value;} MAC_TABLE_ENTRY;
typedef struct {int MacTabLock;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_open_owner wr_iot_peer_open_owner;} RTMP_ADAPTER;
static int held,calls,fail_body,retain_during_body;static MAC_TABLE_ENTRY peer;
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
static MAC_TABLE_ENTRY *wr_iot_wds_insert_transaction_owned(RTMP_ADAPTER *a,UCHAR *addr,UINT index,UINT mode,
 const struct wr_iot_peer_open_ticket *ticket,unsigned long lease){
 (void)addr;assert(!held&&index<MAX_WDS_ENTRY&&mode==2);calls++;
 assert(a->wr_iot_peer_open_owner.active_lease==lease);
 assert(!wr_iot_peer_open_finish(&a->wr_iot_peer_open_owner,&a->wr_iot_peer_table_owner,ticket,1));
 assert(wr_iot_peer_open_insert_admit(&a->wr_iot_peer_open_owner,&a->wr_iot_peer_table_owner,ticket,lease));
 assert(!wr_iot_peer_open_insert_admit(&a->wr_iot_peer_open_owner,&a->wr_iot_peer_table_owner,ticket,lease));
 if(retain_during_body)assert(wr_iot_peer_open_finish(&a->wr_iot_peer_open_owner,&a->wr_iot_peer_table_owner,ticket,0));
 return fail_body?NULL:&peer;
}
#include "wr-iot-wds-startup-transaction.inc"
static RTMP_ADAPTER a;static int dev,other;static UCHAR addr[6];static struct wr_iot_peer_open_ticket t;
static void setup(void){memset(&a,0,sizeof a);held=calls=fail_body=retain_during_body=0;
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);wr_iot_peer_open_owner_init(&a.wr_iot_peer_open_owner);
 assert(wr_iot_peer_open_begin(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&dev,1,&t));
 assert(wr_iot_peer_open_startup(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t));}
int main(void){struct wr_iot_peer_open_ticket bad;
 setup();assert(!wr_iot_wds_insert_startup(NULL,addr,0,&t));
 assert(!wr_iot_wds_insert_startup(&a,NULL,0,&t));
 assert(!wr_iot_wds_insert_startup(&a,addr,MAX_WDS_ENTRY,&t));
 bad=t;bad.device=&other;assert(!wr_iot_wds_insert_startup(&a,addr,0,&bad)&&!calls&&!held);
 bad=t;bad.serial++;assert(!wr_iot_wds_insert_startup(&a,addr,0,&bad)&&!calls&&!held);
 assert(wr_iot_wds_insert_startup(&a,addr,0,&t)==&peer&&calls==1&&!held);
 assert(!a.wr_iot_peer_open_owner.active_lease&&a.wr_iot_peer_table_owner.active);
 assert(wr_iot_wds_insert_startup(&a,addr,1,&t)==&peer&&calls==2);
 assert(wr_iot_peer_open_finish(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t,1));
 setup();fail_body=1;assert(!wr_iot_wds_insert_startup(&a,addr,0,&t)&&!held);
 assert(a.wr_iot_peer_table_owner.retained&&!a.wr_iot_peer_open_owner.active_lease);
 assert(!wr_iot_wds_insert_startup(&a,addr,0,&t)&&calls==1);
 setup();retain_during_body=1;assert(!wr_iot_wds_insert_startup(&a,addr,0,&t));
 assert(a.wr_iot_peer_table_owner.retained&&!a.wr_iot_peer_open_owner.active_lease&&!held);
 return 0;}
