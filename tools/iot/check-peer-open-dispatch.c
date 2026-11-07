#include "peer-open-owner.h"
#include "peer-close-executor.h"
#include "peer-open-request.h"
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
typedef int INT;typedef unsigned int UINT;typedef unsigned long ULONG;
typedef struct {int kind;} ENTRY;
typedef struct {int wr_iot_setup_observed,wr_iot_setup_result;} TR;
typedef struct {int MacTabLock;void *net_dev;unsigned int wr_iot_peer_legacy_close_state;unsigned int wr_iot_peer_delete_active;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_open_owner wr_iot_peer_open_owner;
 struct {unsigned int Size;ENTRY Content[4];TR tr_entry[3];} MacTab;} RTMP_ADAPTER;
static int held,locks;
#define IS_ENTRY_NONE(e) (!(e)->kind)
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!held);held=1;locks++;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(held);held=0;}while(0)
#include "wr-iot-peer-open-dispatch.inc"
static RTMP_ADAPTER a;static int device,other;
static struct wr_iot_peer_open_request request;
static void setup(void){
 memset(&a,0,sizeof a);a.net_dev=&device;held=locks=0;
 wr_iot_peer_table_owner_init(&a.wr_iot_peer_table_owner);
 wr_iot_peer_open_owner_init(&a.wr_iot_peer_open_owner);
 request=(struct wr_iot_peer_open_request){1,WR_PEER_OPEN_BEGIN,&device,0};
}
static int dispatch(void){int r=wr_iot_peer_open_dispatch(&a,&request,sizeof request);assert(!held);return r;}
int main(void){unsigned long serial,lease;struct wr_iot_peer_open_ticket t;
 setup();assert(wr_iot_peer_open_dispatch(NULL,&request,sizeof request)==1&&!locks);
 assert(wr_iot_peer_open_dispatch(&a,NULL,sizeof request)==1&&!locks);
 assert(wr_iot_peer_open_dispatch(&a,&request,sizeof request-1)==1&&!locks);
 request.version=2;assert(dispatch()==1&&!locks);request.version=1;
 request.device=&other;assert(dispatch()==1&&!a.wr_iot_peer_table_owner.active);
 request.device=&device;request.action=999;assert(dispatch()==1);
 request.action=WR_PEER_OPEN_BEGIN;a.MacTab.Size=1;assert(dispatch()==1&&!request.serial);
 a.MacTab.Size=0;a.MacTab.Content[3].kind=1;assert(dispatch()==1&&!request.serial);
 a.MacTab.Content[3].kind=0;a.MacTab.tr_entry[2]=(TR){1,-2};assert(dispatch()==1&&!request.serial);
 a.MacTab.tr_entry[2]=(TR){0};assert(!dispatch());serial=request.serial;assert(serial);
 assert(dispatch()==1&&request.serial==serial);request.action=WR_PEER_OPEN_DONE;assert(dispatch()==1);
 request.action=WR_PEER_OPEN_START;request.serial=serial+1;assert(dispatch()==1);
 request.serial=serial;assert(!dispatch());t=(struct wr_iot_peer_open_ticket){&device,serial};
 lease=wr_iot_peer_open_insert_begin(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t);assert(lease);
 request.action=WR_PEER_OPEN_DONE;assert(dispatch()==1&&a.wr_iot_peer_table_owner.active);
 assert(wr_iot_peer_open_insert_end(&a.wr_iot_peer_open_owner,&a.wr_iot_peer_table_owner,&t,lease));
 assert(!dispatch()&&!a.wr_iot_peer_table_owner.active);assert(dispatch()==1);
 request=(struct wr_iot_peer_open_request){1,WR_PEER_OPEN_BEGIN,&device,0};assert(!dispatch());
 request.action=WR_PEER_OPEN_FAIL;assert(!dispatch()&&a.wr_iot_peer_table_owner.retained);
 request.action=WR_PEER_OPEN_DONE;assert(dispatch()==1);
 request.action=WR_PEER_OPEN_BEGIN;request.serial=0;assert(dispatch()==1);
 setup();a.wr_iot_peer_table_owner.serial=~0UL;assert(dispatch()==1&&a.wr_iot_peer_table_owner.poisoned);
 return 0;
}
