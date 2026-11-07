#include "interface-registry.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do{if(!(x)){fprintf(stderr,"failed %d: %s\n",__LINE__,#x);exit(42);}}while(0)
#define MT_MAC 1
#define WDS_SUPPORT 1
#define WDEV_NUM_MAX 1
typedef void VOID;typedef unsigned long ULONG;typedef unsigned int UINT;typedef int INT;
struct wifi_dev {void *if_dev;};
typedef struct {struct wifi_dev *wdev;unsigned char Addr[6];} MAC_TABLE_ENTRY;
typedef struct {int wr_iot_transition_lock;struct wr_iot_interface_ref wr_iot_interface_refs[2];} RTMP_ADAPTER;
static int locked;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;CHECK(!locked);locked=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);CHECK(locked);locked=0;}while(0)
#include "wr-iot-wds-hardware-delete-observer.inc"
int main(void)
{
 RTMP_ADAPTER a={0};int device=0;
 struct wifi_dev w={&device};MAC_TABLE_ENTRY peer={&w,{1,2,3,4,5,6}};
 struct wr_iot_interface_ref *r=&a.wr_iot_interface_refs[0];
 unsigned long serial;
 wr_iot_ref_init(r,&device,1);r->published=1;r->family=WR_REF_FAMILY_WDS;
 CHECK(wr_iot_wds_peer_operation_begin_remove(&r->peer_operation,&device,1));
 serial=wr_iot_wds_retirement_save(&r->peer_operation,&device,1,0,1,peer.Addr);CHECK(serial);
 wr_iot_wds_record_hardware_delete(&a,&peer,2,-2);
 CHECK(!locked&&!r->peer_operation.retirement_hardware_observed);
 peer.Addr[0]^=1;wr_iot_wds_record_hardware_delete(&a,&peer,1,-2);
 CHECK(!locked&&!r->peer_operation.retirement_hardware_observed);peer.Addr[0]^=1;
 r->generation=2;wr_iot_wds_record_hardware_delete(&a,&peer,1,-2);
 CHECK(!locked&&!r->peer_operation.retirement_hardware_observed);r->generation=1;
 wr_iot_wds_record_hardware_delete(&a,&peer,1,-2);
 CHECK(!locked&&r->peer_operation.retirement_hardware_observed&&r->peer_operation.retirement_hardware_result==-2);
 wr_iot_wds_record_hardware_delete(&a,&peer,1,0);
 CHECK(r->peer_operation.retirement_hardware_result==-2); /* first result immutable */
 CHECK(wr_iot_wds_retirement_retain(&r->peer_operation,serial));
 wr_iot_wds_record_hardware_delete(&a,&peer,1,0);
 CHECK(r->peer_operation.retirement_hardware_result==-2&&!locked);
 puts("PASS exact WDS retirement hardware observation");return 0;
}
