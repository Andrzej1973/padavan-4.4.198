#!/usr/bin/env python3
"""Exercise actual resume admission/observer/result and extracted finish checkpoint."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'mgmt/mgmt_entrytb.c').read_text()
signature='static BOOLEAN wr_iot_mac_delete_entry_body(' if 'static BOOLEAN wr_iot_mac_delete_entry_body(' in s else 'static BOOLEAN wr_iot_mac_delete_entry('
start=s.index(signature);end=s.index('\nBOOLEAN MacTableDeleteEntry(',start)
body=s[start:end]
assert body.index('wr-iot-wds-delete-resume-admission.inc')<body.index('BndStrg_UpdateEntry')
assert body.index('wr_iot_wds_hardware_checkpoint:')<body.index('wr-iot-wds-hardware-delete-result.inc')
first=body.index('#if defined(MT_MAC) && defined(WDS_SUPPORT)\n if (wr_resume_owner)')
last=body.index('\n\tNdisReleaseSpinLock(&pAd->MacTabLock);\n\t/*Update TX burst',first)
finish=body[first:last]
prefix=r'''
#include "interface-registry.h"
#include <assert.h>
#include <string.h>
#define MT_MAC 1
#define WDS_SUPPORT 1
#define WDEV_NUM_MAX 1
#define MAX_LEN_OF_TR_TABLE 4
#define WCID_ALL 255
#define WR_IOT_WCID_APPLIED 0
#define WR_IOT_WCID_NOT_WRITTEN -1
#define FALSE 0
typedef int BOOLEAN;typedef unsigned int UINT;typedef unsigned long ULONG;typedef int INT;typedef void VOID;typedef unsigned char UCHAR;
struct wifi_dev {void *if_dev;};
typedef struct {int kind;struct wifi_dev *wdev;unsigned char Addr[6];} MAC_TABLE_ENTRY;
typedef struct {int enq_cap,deq_cap;} STA_TR_ENTRY;
typedef struct {int MacTabLock,wr_iot_transition_lock;struct wr_iot_interface_ref wr_iot_interface_refs[2];} RTMP_ADAPTER;
static int locks,notifications,timers,ba,hardware,software,result;
#define READ_ONCE(v) (v)
#define IS_ENTRY_WDS(e) ((e)->kind==1)
#define IS_ENTRY_NONE(e) ((e)->kind==0)
#define MAC_ADDR_EQUAL(a,b) (!memcmp((a),(b),6))
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(locks==1);locks=2;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(locks==2);locks=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(locks==1);locks=0;}while(0)
#define wr_iot_delete_wcid_checked(a,w) ((void)(a),(void)(w),hardware++,result)
#define RTMP_STA_ENTRY_MAC_RESET(a,w) do{(void)(a);(void)(w);assert(0);}while(0)
#include "wr-iot-wds-hardware-delete-observer.inc"
static int deletion(RTMP_ADAPTER *pAd,MAC_TABLE_ENTRY *pEntry,STA_TR_ENTRY *tr_entry,
 UINT wcid,UCHAR *pAddr,const void *wr_resume_device,unsigned long wr_resume_generation,unsigned long wr_resume_serial)
{
 struct wifi_dev *wdev=0;struct wr_iot_interface_ref *wr_resume_owner=0;
#include "wr-iot-wds-delete-resume-admission.inc"
#include "wr-iot-wds-peer-delete-gate.inc"
 notifications++;timers++;ba++;
wr_iot_wds_hardware_checkpoint: ;
#include "wr-iot-wds-hardware-delete-result.inc"
 software++;pEntry->kind=0;(void)wdev;
'''
suffix=r'''
 NdisReleaseSpinLock(&pAd->MacTabLock);return 1;
}
static RTMP_ADAPTER a;static MAC_TABLE_ENTRY peer;static STA_TR_ENTRY tr;
static int device;static struct wifi_dev w={&device};static unsigned char address[6]={1,2,3,4,5,6};
static unsigned long serial;
static void setup(void){
 struct wr_iot_interface_ref *r;
 memset(&a,0,sizeof a);peer=(MAC_TABLE_ENTRY){1,&w,{1,2,3,4,5,6}};tr=(STA_TR_ENTRY){0};
 locks=1;notifications=timers=ba=hardware=software=0;result=0;r=&a.wr_iot_interface_refs[0];
 wr_iot_ref_init(r,&device,7);r->published=1;r->family=WR_REF_FAMILY_WDS;r->phase=WR_REF_OWNED;
 assert(wr_iot_wds_peer_operation_begin_remove(&r->peer_operation,&device,7));
 serial=wr_iot_wds_retirement_save(&r->peer_operation,&device,7,0,1,address);assert(serial);
 assert(wr_iot_wds_retirement_hardware_result(&r->peer_operation,serial,-1));
 assert(wr_iot_wds_retirement_retain(&r->peer_operation,serial));
}
static int resume(unsigned long gen,unsigned long token){return deletion(&a,&peer,&tr,1,address,&device,gen,token);}
int main(void){
 setup();assert(!deletion(&a,&peer,&tr,1,address,0,0,0)&&!locks&&!notifications&&!hardware);
 setup();assert(resume(7,serial)&&!locks&&!notifications&&!timers&&!ba&&hardware==1&&software==1);
 assert(a.wr_iot_interface_refs[0].peer_operation.retirement_stage==4&&a.wr_iot_interface_refs[0].peer_operation.removing);
 locks=1;assert(!resume(7,serial)&&!locks&&hardware==1&&software==1);
 setup();assert(!resume(8,serial)&&!locks&&!hardware&&!notifications);
 setup();assert(!resume(7,serial+1)&&!locks&&!hardware&&!notifications);
 setup();tr.enq_cap=1;assert(!resume(7,serial)&&!locks&&!hardware);
 setup();peer.Addr[0]^=1;assert(!resume(7,serial)&&!locks&&!hardware);
 setup();a.wr_iot_interface_refs[0].peer_operation.retirement_hardware_observed=0;
 assert(!resume(7,serial)&&!locks&&!hardware);
 setup();a.wr_iot_interface_refs[0].peer_operation.retirement_hardware_result=-2;
 assert(!resume(7,serial)&&!locks&&!hardware);
 setup();result=-2;assert(!resume(7,serial)&&!locks&&hardware==1&&!software&&!notifications);
 assert(a.wr_iot_interface_refs[0].peer_operation.retirement_stage==2);
 locks=1;assert(!resume(7,serial)&&!locks&&hardware==1);
 setup();result=-1;assert(!resume(7,serial)&&!locks&&hardware==1&&!software);
 locks=1;result=0;assert(resume(7,serial)&&!locks&&hardware==2&&software==1&&!notifications&&!timers&&!ba);
 assert(a.wr_iot_interface_refs[0].peer_operation.retirement_retry_count==2);
 return 0;
}
'''
a.output.write_text(prefix+finish+suffix,encoding='utf-8')
print('Extracted resume checkpoint flow; vendor cleanup/locks are injected')
