/* Regression contract for whole-delete wrappers: existing WDS resume must
 * reach its exact checkpoint after NOT_WRITTEN. No real hardware is modeled. */
#include "peer-table-owner.h"
#include "peer-close-executor.h"
#include <stddef.h>
#include <stdio.h>
#include <assert.h>
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 4
#define FALSE 0
typedef int BOOLEAN;typedef unsigned short USHORT;typedef unsigned char UCHAR;
typedef struct {int MacTabLock;unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;} RTMP_ADAPTER;
static int calls;
static BOOLEAN wr_iot_mac_delete_entry(RTMP_ADAPTER *,USHORT,UCHAR *,const void *,unsigned long,unsigned long,unsigned long);
#define NdisAcquireSpinLock(l) ((void)(l))
#define NdisReleaseSpinLock(l) ((void)(l))
static BOOLEAN wr_iot_mac_delete_entry_body(RTMP_ADAPTER *a,USHORT w,UCHAR *addr,
 const void *device,unsigned long generation,unsigned long resume,unsigned long table){
 (void)a;(void)w;(void)addr;(void)table;calls++;
 /* Active lease assertions are enabled by the checker build for candidate58. */
#ifdef TEST_DELETE_EXECUTION_LEASE
 if(!table){
  int before=calls;assert(a->wr_iot_peer_delete_active==1);
  assert(!wr_iot_mac_delete_entry(a,w,addr,device,generation,resume,0)&&calls==before);
 }else assert(!a->wr_iot_peer_delete_active&&wr_iot_peer_table_allows(&a->wr_iot_peer_table_owner,table));
#endif
 if(!resume)return FALSE; /* Model retained NOT_WRITTEN hardware result. */
 return device&&generation==7&&resume==19;
}
#include "wr-iot-peer-normal-delete.inc"
int main(void){RTMP_ADAPTER a={0};UCHAR addr[6]={1,2,3,4,5,6};int device;
 if(wr_iot_mac_delete_entry(&a,1,addr,NULL,0,0,0))return 2;
 if(!wr_iot_mac_delete_entry(&a,1,addr,&device,7,19,0)||calls!=2){
  fprintf(stderr,"REGRESSION: retained ordinary table owner blocks existing WDS checkpoint resume; body calls=%d\n",calls);
  return 1;
 }
#ifdef TEST_DELETE_EXECUTION_LEASE
 assert(!a.wr_iot_peer_delete_active&&!a.wr_iot_peer_table_owner.active);
 {unsigned long parent=wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner);assert(parent);
 assert(wr_iot_mac_delete_entry(&a,1,addr,&device,7,19,parent));
 assert(a.wr_iot_peer_table_owner.active&&!a.wr_iot_peer_delete_active);
 assert(wr_iot_peer_table_finish(&a.wr_iot_peer_table_owner,parent,1));}
#endif
 puts("PASS existing WDS checkpoint resume remains reachable");return 0;
}
