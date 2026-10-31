#include "peer-open-owner.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define TRUE 1
#define FALSE 0
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
typedef int BOOLEAN;typedef unsigned int UINT;
typedef struct {int kind;} ENTRY;
typedef struct {int wr_iot_setup_observed,wr_iot_setup_result;} TR;
typedef struct {unsigned int Size;ENTRY Content[4];TR tr_entry[3];} MAC_TABLE;
typedef struct {int MacTabLock;MAC_TABLE MacTab;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 unsigned long wr_iot_peer_close_serial;} RTMP_ADAPTER;
static int held,clears;
#define IS_ENTRY_NONE(e) (!(e)->kind)
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#define NdisZeroMemory(p,n) do{assert(held);memset(p,0,n);clears++;}while(0)
#include "wr-iot-peer-close-table.inc"
int main(void){RTMP_ADAPTER a={0};struct wr_iot_peer_open_owner open;
 struct wr_iot_peer_open_ticket ticket;int dev;unsigned long serial;
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);
 assert(!wr_iot_peer_close_clear(&a)&&!clears&&!held);
 assert(!wr_iot_peer_close_finish(&a)&&!held);
 a.MacTab.Size=1;assert(!wr_iot_peer_close_hold(&a)&&!held);a.MacTab.Size=0;
 a.MacTab.Content[3].kind=1;assert(!wr_iot_peer_close_hold(&a)&&!held);a.MacTab.Content[3].kind=0;
 a.MacTab.tr_entry[2]=(TR){1,-2};assert(!wr_iot_peer_close_hold(&a)&&!held);a.MacTab.tr_entry[2]=(TR){0};
 assert(wr_iot_peer_table_transaction_enter(&a.wr_iot_peer_table_owner));
 assert(!wr_iot_peer_close_hold(&a)&&!held);
 assert(wr_iot_peer_table_transaction_leave(&a.wr_iot_peer_table_owner));
 assert(wr_iot_peer_close_hold(&a)&&!held);serial=a.wr_iot_peer_close_serial;assert(serial);
 assert(wr_iot_peer_close_hold(&a)&&a.wr_iot_peer_close_serial==serial);
 assert(!wr_iot_peer_table_allows(&a.wr_iot_peer_table_owner,0));
 assert(!wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner));
 a.wr_iot_peer_close_serial++;assert(!wr_iot_peer_close_clear(&a)&&!clears);
 a.wr_iot_peer_close_serial=serial;
 assert(wr_iot_peer_close_clear(&a)&&clears==1&&a.wr_iot_peer_table_owner.active&&!held);
 assert(wr_iot_peer_close_finish(&a)&&!held&&!a.wr_iot_peer_close_serial);
 assert(a.wr_iot_peer_table_owner.closed&&!a.wr_iot_peer_table_owner.active);
 assert(!wr_iot_peer_close_hold(&a)&&!held);
 assert(!wr_iot_peer_table_transaction_enter(&a.wr_iot_peer_table_owner));
 assert(!wr_iot_peer_table_begin(&a.wr_iot_peer_table_owner));
 wr_iot_peer_open_owner_init(&open);
 assert(wr_iot_peer_open_begin(&open,&a.wr_iot_peer_table_owner,&dev,1,&ticket));
 assert(ticket.serial>serial&&!a.wr_iot_peer_table_owner.closed);
 assert(wr_iot_peer_open_finish(&open,&a.wr_iot_peer_table_owner,&ticket,0));
 assert(!wr_iot_peer_close_hold(&a)&&!held);
 return 0;
}
