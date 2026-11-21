#include "aux-close-claim.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define CHECK(x) do { if(!(x)){fprintf(stderr,"failed line %d: %s\n",__LINE__,#x);exit(42);} } while(0)
#define MAX_WDS_ENTRY 2
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 3
#define WDEV_NUM_MAX 2
#define MAC_ADDR_LEN 6
#define MAC_TABLE_AGEOUT_TIME 10
#define WDS_LAZY_MODE 3
#define WR_IOT_WCID_NOT_WRITTEN (-1)
#define READ_ONCE(v) (v)
#ifdef TEST_WDS_RECOVERY
#define MT_MAC 1
#define WDS_SUPPORT 1
#endif
#define TRUE 1
#define FALSE 0
typedef int BOOLEAN;
typedef void VOID;
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef unsigned char UCHAR;
typedef unsigned short USHORT;
struct net_device {int refs;};
typedef struct net_device *PNET_DEV;
struct wifi_dev {PNET_DEV if_dev;};
typedef struct {int Valid;USHORT MacTabMatchWCID;UCHAR PeerWdsAddr[6];struct wifi_dev wdev;} RT_802_11_WDS_ENTRY;
typedef struct {int kind;USHORT wcid;struct wifi_dev *wdev;UCHAR Addr[6];unsigned int NoDataIdleCount;} MAC_TABLE_ENTRY;
typedef struct {
 int WdsTabLock,MacTabLock,wr_iot_transition_lock,wr_iot_ticket_wait;
 struct {int Mode;unsigned int Size;RT_802_11_WDS_ENTRY WdsEntry[2];} WdsTab;
 struct {MAC_TABLE_ENTRY Content[4];struct {unsigned int NoDataIdleCount;int enq_cap,deq_cap;} tr_entry[3];} MacTab;
 struct wr_iot_interface_ref wr_iot_interface_refs[3];
 struct wr_iot_radio_transition wr_iot_transition;
} RTMP_ADAPTER;
static int locks,mode,calls,wakes;
#define NdisAcquireSpinLock(l) do{(void)(l);CHECK(locks<2);locks++;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);CHECK(locks>0&&locks<=2);locks--;}while(0)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;CHECK(locks==2);locks=3;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);CHECK(locks==3);locks=2;}while(0)
#define IS_ENTRY_WDS(p) ((p)->kind==1)
#define IS_ENTRY_NONE(p) ((p)->kind==0)
#define MAC_ADDR_EQUAL(a,b) (!memcmp((a),(b),6))
#define COPY_MAC_ADDR(a,b) memcpy((a),(b),6)
#define NdisZeroMemory(a,n) memset((a),0,(n))
static void dev_hold(struct net_device *d){CHECK(locks==3);d->refs++;}
static void dev_put(struct net_device *d){CHECK(!locks&&d->refs==1);d->refs--;}
static void wake_up_all(int *w){(void)w;CHECK(!locks);wakes++;}
#ifdef TEST_WDS_RECOVERY
static int resume_calls,resume_result;
static BOOLEAN wr_iot_wds_resume_delete(RTMP_ADAPTER *a,USHORT wcid,UCHAR *addr,
 const void *device,unsigned long generation,unsigned long serial)
{
 struct wr_iot_wds_peer_operation *o=&a->wr_iot_interface_refs[0].peer_operation;
 CHECK(!locks&&((const struct net_device *)device)->refs==1);
 CHECK(wr_iot_wds_retirement_claim_no_write(o,device,generation,serial,o->retirement_index,wcid,addr));
 resume_calls++;
 CHECK(wr_iot_wds_retirement_hardware_result(o,serial,resume_result));
 if(resume_result)return FALSE;
 a->MacTab.Content[wcid].kind=0;
 CHECK(wr_iot_wds_retirement_software_done(o,serial));return TRUE;
}
#endif
static BOOLEAN MacTableDeleteWDSEntry(RTMP_ADAPTER *a,USHORT wcid,UCHAR *addr)
{
 struct wr_iot_interface_ref *r=&a->wr_iot_interface_refs[0];
 CHECK(!locks&&r->peer_operation.removing&&a->wr_iot_transition.active_tx==1);
 CHECK(r->peer_operation.retirement_stage==1&&r->peer_operation.retirement_serial==1);
 CHECK(r->peer_operation.retirement_wcid==wcid&&MAC_ADDR_EQUAL(r->peer_operation.retirement_address,addr));
 CHECK(!wr_iot_wds_peer_operation_enter(&r->peer_operation,r->device,r->generation));
 CHECK(!wr_iot_ref_begin_close(r,r->device,r->generation,r->last_token));
 CHECK(wcid==1&&MAC_ADDR_EQUAL(addr,a->MacTab.Content[1].Addr));calls++;
#ifdef TEST_WDS_RECOVERY
 CHECK(wr_iot_wds_retirement_hardware_result(&r->peer_operation,
       r->peer_operation.retirement_serial,mode==1?-1:0));
#endif
 if(mode==1)return FALSE;
 if(mode==2)return TRUE; /* vendor TRUE without deletion */
 a->MacTab.Content[1].kind=0;
 if(mode==3)a->WdsTab.WdsEntry[0].PeerWdsAddr[0]^=1;
 if(mode==4)a->MacTab.Content[1].kind=2; /* another peer occupies WCID */
 if(mode==5)r->generation++; /* injected identity corruption: retain */
 if(mode==6)a->WdsTab.WdsEntry[0].MacTabMatchWCID=2;
 return TRUE;
}
#include "wr-iot-wds-ageout-transaction.inc"
static void setup(RTMP_ADAPTER *a,struct net_device *dev)
{
 struct wr_iot_interface_ref *r;
 unsigned char addr[6]={1,2,3,4,5,6};
 memset(a,0,sizeof *a);locks=mode=calls=wakes=0;dev->refs=0;
#ifdef TEST_WDS_RECOVERY
 resume_calls=resume_result=0;
#endif
 a->WdsTab.Mode=WDS_LAZY_MODE;a->WdsTab.Size=1;
 a->WdsTab.WdsEntry[0].Valid=1;a->WdsTab.WdsEntry[0].MacTabMatchWCID=1;
 a->WdsTab.WdsEntry[0].wdev.if_dev=dev;
 COPY_MAC_ADDR(a->WdsTab.WdsEntry[0].PeerWdsAddr,addr);
 a->MacTab.Content[1]=(MAC_TABLE_ENTRY){1,1,&a->WdsTab.WdsEntry[0].wdev,{1,2,3,4,5,6},10};
 r=&a->wr_iot_interface_refs[0];wr_iot_ref_init(r,dev,1);
 r->family=WR_REF_FAMILY_WDS;r->published=1;r->phase=WR_REF_OWNED;r->last_token=1;
 wr_iot_radio_transition_init(&a->wr_iot_transition);
 a->wr_iot_transition.phase=WR_RADIO_READY;a->wr_iot_transition.main_ready=1;
}
int main(void)
{
 RTMP_ADAPTER a;struct net_device dev;int i;
 setup(&a,&dev);CHECK(wr_iot_wds_ageout(&a,0));
 CHECK(!locks&&!dev.refs&&calls==1&&wakes==1&&!a.WdsTab.Size&&!a.WdsTab.WdsEntry[0].Valid);
 CHECK(!a.wr_iot_interface_refs[0].peer_operation.removing&&!a.wr_iot_transition.active_tx);
 CHECK(!a.wr_iot_interface_refs[0].peer_operation.retirement_stage);
 for(i=1;i<=6;i++){
  setup(&a,&dev);mode=i;CHECK(!wr_iot_wds_ageout(&a,0));
  CHECK(!locks&&!dev.refs&&calls==1&&a.WdsTab.Size==1&&a.WdsTab.WdsEntry[0].Valid);
  CHECK(a.wr_iot_interface_refs[0].peer_operation.removing&&a.wr_iot_transition.active_tx==1);
  CHECK(a.wr_iot_interface_refs[0].peer_operation.retirement_stage==2);
 }
 setup(&a,&dev);a.wr_iot_interface_refs[0].peer_operation.active=1;
 CHECK(!wr_iot_wds_ageout(&a,0)&&!calls&&!locks&&!a.wr_iot_interface_refs[0].peer_operation.removing);
 setup(&a,&dev);a.wr_iot_transition.busy=WR_RADIO_AUX_CLOSE;
 CHECK(!wr_iot_wds_ageout(&a,0)&&!calls&&!locks&&!a.wr_iot_interface_refs[0].peer_operation.removing);
 setup(&a,&dev);a.WdsTab.WdsEntry[0].MacTabMatchWCID=MAX_LEN_OF_MAC_TABLE;
 CHECK(!wr_iot_wds_ageout(&a,0)&&!calls&&!locks);
 setup(&a,&dev);a.MacTab.Content[1].NoDataIdleCount=0;
 CHECK(!wr_iot_wds_ageout(&a,0)&&!calls&&!locks);
 CHECK(!wr_iot_wds_ageout(&a,MAX_WDS_ENTRY));CHECK(!wr_iot_wds_ageout(NULL,0));
 setup(&a,&dev);a.wr_iot_interface_refs[0].peer_operation.retirement_serial=~0UL;
 CHECK(!wr_iot_wds_ageout(&a,0)&&!calls&&!locks&&!dev.refs);
 CHECK(!a.wr_iot_interface_refs[0].peer_operation.removing&&!a.wr_iot_transition.active_tx);
 setup(&a,&dev);a.MacTab.Content[1].NoDataIdleCount=8;
 wr_iot_wds_lazy_maintenance(&a);
 CHECK(!calls&&!locks&&a.MacTab.Content[1].NoDataIdleCount==9&&a.MacTab.tr_entry[1].NoDataIdleCount==1);
 wr_iot_wds_lazy_maintenance(&a);CHECK(calls==1&&!a.WdsTab.Size&&!locks);
 setup(&a,&dev);a.WdsTab.WdsEntry[0].MacTabMatchWCID=3;
 wr_iot_wds_lazy_maintenance(&a);CHECK(!calls&&!locks); /* MAC-valid, TR-invalid */
 setup(&a,&dev);a.WdsTab.WdsEntry[0].PeerWdsAddr[0]^=1;
 wr_iot_wds_lazy_maintenance(&a);CHECK(!calls&&!locks&&!a.MacTab.tr_entry[1].NoDataIdleCount);
 setup(&a,&dev);a.WdsTab.WdsEntry[1]=a.WdsTab.WdsEntry[0];a.WdsTab.WdsEntry[0].Valid=0;
 a.MacTab.Content[1].wdev=&a.WdsTab.WdsEntry[1].wdev;
 wr_iot_wds_lazy_maintenance(&a);CHECK(calls==1&&!a.WdsTab.Size&&!a.WdsTab.WdsEntry[1].Valid);
 setup(&a,&dev);mode=1;a.MacTab.Content[1].NoDataIdleCount=~0U;
 a.MacTab.tr_entry[1].NoDataIdleCount=~0U;
 wr_iot_wds_lazy_maintenance(&a);wr_iot_wds_lazy_maintenance(&a);
#ifndef TEST_WDS_RECOVERY
 CHECK(calls==1&&!locks&&a.MacTab.Content[1].NoDataIdleCount==~0U&&a.MacTab.tr_entry[1].NoDataIdleCount==~0U);
#endif
#ifdef TEST_WDS_RECOVERY
 setup(&a,&dev);mode=1;CHECK(!wr_iot_wds_ageout(&a,0));
 CHECK(wr_iot_wds_recover_ageout(&a,0)&&resume_calls==1&&!a.WdsTab.Size&&!dev.refs&&!locks);
 CHECK(!a.wr_iot_transition.active_tx&&!a.wr_iot_interface_refs[0].peer_operation.removing);
 CHECK(!wr_iot_wds_recover_ageout(&a,0)&&resume_calls==1);
 setup(&a,&dev);mode=1;CHECK(!wr_iot_wds_ageout(&a,0));resume_result=-1;
 CHECK(wr_iot_wds_recover_ageout(&a,0)&&resume_calls==1&&a.WdsTab.Size==1&&a.wr_iot_transition.active_tx==1);
 resume_result=0;CHECK(wr_iot_wds_recover_ageout(&a,0)&&resume_calls==2&&!a.WdsTab.Size&&!a.wr_iot_transition.active_tx);
 setup(&a,&dev);mode=1;CHECK(!wr_iot_wds_ageout(&a,0));resume_result=-2;
 CHECK(wr_iot_wds_recover_ageout(&a,0)&&resume_calls==1);
 CHECK(wr_iot_wds_recover_ageout(&a,0)&&resume_calls==1&&a.WdsTab.Size==1&&a.wr_iot_transition.active_tx==1);
 setup(&a,&dev);mode=1;CHECK(!wr_iot_wds_ageout(&a,0));a.WdsTab.WdsEntry[0].PeerWdsAddr[0]^=1;
 CHECK(wr_iot_wds_recover_ageout(&a,0)&&!resume_calls&&a.WdsTab.Size==1&&a.wr_iot_transition.active_tx==1);
 setup(&a,&dev);mode=1;CHECK(!wr_iot_wds_ageout(&a,0));
 wr_iot_wds_lazy_maintenance(&a);CHECK(resume_calls==1&&!a.WdsTab.Size&&!a.wr_iot_transition.active_tx);
 setup(&a,&dev);mode=1;CHECK(!wr_iot_wds_ageout(&a,0));
 {struct wr_iot_wds_peer_operation *o=&a.wr_iot_interface_refs[0].peer_operation;
  CHECK(wr_iot_wds_retirement_claim_no_write(o,&dev,1,o->retirement_serial,0,1,o->retirement_address));
  CHECK(wr_iot_wds_retirement_hardware_result(o,o->retirement_serial,0));
  a.MacTab.Content[1].kind=0;CHECK(wr_iot_wds_retirement_software_done(o,o->retirement_serial));
  a.wr_iot_transition.active_tx=0;
  CHECK(wr_iot_wds_recover_ageout(&a,0)&&!resume_calls&&a.WdsTab.Size==1&&o->retirement_stage==4);
  a.wr_iot_transition.active_tx=1;
  CHECK(wr_iot_wds_recover_ageout(&a,0)&&!resume_calls&&!a.WdsTab.Size&&!o->retirement_stage&&!dev.refs);
 }
 setup(&a,&dev);mode=1;CHECK(!wr_iot_wds_ageout(&a,0));
 a.wr_iot_interface_refs[1]=a.wr_iot_interface_refs[0];
 CHECK(wr_iot_wds_recover_ageout(&a,0)&&!resume_calls&&a.WdsTab.Size==1&&a.wr_iot_transition.active_tx==1);
#endif
 puts("PASS WDS age-out reservation and terminal-state refusal");return 0;
}
