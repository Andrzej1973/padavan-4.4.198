#!/usr/bin/env python3
"""Extract actual reset loops to test refusal ordering, not atomic reset/lifetime."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'mgmt/mgmt_entrytb.c').read_text()
def extract(anchor):
 start=s.index(anchor);brace=s.index('{',start);depth=0
 for end in range(brace,len(s)):
  if s[end]=='{':depth+=1
  elif s[end]=='}':
   depth-=1
   if not depth:return s[start:end+1]
 raise ValueError(anchor)
delete=extract('static BOOLEAN wr_iot_mac_delete_entry_body(' if 'static BOOLEAN wr_iot_mac_delete_entry_body(' in s else 'static BOOLEAN wr_iot_mac_delete_entry(')
assert delete.index('wr-iot-peer-failed-delete-gate.inc')<delete.index('wr-iot-wds-delete-resume-admission.inc')<delete.index('RTMPCancelTimer')
checked='BOOLEAN MacTableReset(' in s
result_type='BOOLEAN' if checked else 'VOID'
functions=extract(result_type+' MacTableReset(')+'\n'+extract(result_type+' MacTableResetWdev(')
prefix=r'''
#include <assert.h>
#include <stddef.h>
#include <string.h>
#define CONFIG_AP_SUPPORT 1
#define TRUE 1
#define FALSE 0
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_TR_TABLE 4
#define MAC_ADDR_LEN 6
#define MAIN_MBSSID 0
#define EAPOL_START_DISABLE 0
#define SST_ASSOC 1
#define NDIS_STATUS_SUCCESS 0
#define REASON_NO_LONGER_VALID 1
#define SUBTYPE_DEAUTH 1
#define END_OF_ARGS 0
#define RT_DEBUG_TRACE 0
#define RT_DEBUG_OFF 0
#define DBGPRINT(l,a) do{(void)(l);}while(0)
typedef int BOOLEAN;typedef int INT;typedef unsigned int UINT;typedef unsigned char UCHAR;typedef unsigned short USHORT;typedef unsigned long ULONG;typedef void VOID;typedef int NDIS_STATUS;
typedef struct {int dummy;} HEADER_802_11;
struct wifi_dev {int func_idx;UCHAR if_addr[6],bssid[6];};
typedef struct {int kind,Sst,EnqueueStartForPSKTimer,EnqueueEapolStartTimerRunning;UCHAR Addr[6];struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
typedef struct {int wr_iot_setup_observed,wr_iot_setup_result;} STA_TR_ENTRY;
typedef struct {unsigned int Number;} QUEUE_HEADER;
typedef struct {MAC_TABLE_ENTRY Content[4];STA_TR_ENTRY tr_entry[4];unsigned int Size;QUEUE_HEADER McastPsQueue;} MAC_TABLE;
typedef struct {int MacTabLock,irq_lock;unsigned int wr_iot_peer_delete_active;MAC_TABLE MacTab;struct {int BssidNum;struct {int StaCount;} MBSSID[2];} ApCfg;} RTMP_ADAPTER;
static int mac,irq,released,deleted,delete_ok=1,alloc_fail;
static UCHAR buffer[64];
#define NdisAcquireSpinLock(l) do{(void)(l);assert(!mac&&!irq);mac=1;}while(0)
#define NdisReleaseSpinLock(l) do{(void)(l);assert(mac&&!irq);mac=0;}while(0)
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!mac&&!irq);irq=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(irq);irq=0;}while(0)
#define RTMPReleaseTimer(t,c) do{(void)(t);*(c)=1;released++;}while(0)
#define IS_ENTRY_CLIENT(e) ((e)->kind==1)
#define IS_ENTRY_APCLI(e) ((e)->kind==2)
#define IF_DEV_CONFIG_OPMODE_ON_AP(a) if((void)(a),1)
#define MlmeAllocateMemory(a,p) ((void)(a),*(p)=buffer,alloc_fail)
#define MgtMacHeaderInit(a,h,...) do{(void)(a);(void)(h);}while(0)
static void fake_frame(UCHAR *b,ULONG *len,...){(void)b;(void)len;}
#define MakeOutgoingFrame fake_frame
#define MiniportMMRequest(a,q,b,n) do{(void)(a);(void)(q);(void)(b);(void)(n);}while(0)
#define MlmeFreeMemory(a,b) do{(void)(a);(void)(b);}while(0)
#define RtmpusecDelay(n) ((void)(n))
#define APCleanupPsQueue(a,q) do{(void)(a);(q)->Number=0;}while(0)
#define NdisZeroMemory(p,n) memset((p),0,(n))
#define Offsetof(t,m) offsetof(t,m)
#define InitializeQueueHeader(q) ((q)->Number=0)
static BOOLEAN MacTableDeleteEntry(RTMP_ADAPTER *a,int i,UCHAR *addr){
 (void)addr;deleted++;if(!delete_ok)return FALSE;
 if(a->MacTab.Content[i].kind){a->MacTab.Content[i].kind=0;a->MacTab.Size--;}
 return TRUE;
}
#include "wr-iot-peer-failed-reset-preflight.inc"
static BOOLEAN ordinary_delete(RTMP_ADAPTER *pAd,STA_TR_ENTRY *tr_entry){
#include "wr-iot-peer-failed-delete-gate.inc"
 return TRUE;
}
'''
suffix=r'''
static void setup(RTMP_ADAPTER *a,struct wifi_dev *w){
 memset(a,0,sizeof *a);mac=irq=released=deleted=0;delete_ok=1;
 a->ApCfg.BssidNum=2;a->ApCfg.MBSSID[0].StaCount=1;a->ApCfg.MBSSID[1].StaCount=1;
 a->MacTab.Content[1].kind=1;a->MacTab.Content[1].wdev=w;a->MacTab.Size=1;
}
int main(void){RTMP_ADAPTER a;struct wifi_dev one={0},two={.func_idx=1};
setup(&a,&one);a.MacTab.tr_entry[1]=(STA_TR_ENTRY){1,-2};mac=1;
assert(!ordinary_delete(&a,&a.MacTab.tr_entry[1])&&!mac&&!released&&!deleted);
MacTableReset(&a,1);assert(!released&&!deleted&&a.MacTab.Size==1&&a.ApCfg.MBSSID[0].StaCount==1);
MacTableResetWdev(&a,&one);assert(!released&&!deleted&&a.ApCfg.MBSSID[0].StaCount==1);
MacTableResetWdev(&a,&two);assert(!released&&a.ApCfg.MBSSID[1].StaCount==0&&a.MacTab.Size==1);
setup(&a,&one);delete_ok=0;MacTableReset(&a,1);
assert(released==1&&deleted==1&&a.MacTab.Size==1&&a.ApCfg.MBSSID[0].StaCount==1);
setup(&a,&one);delete_ok=0;MacTableResetWdev(&a,&one);
assert(released==1&&deleted==1&&a.ApCfg.MBSSID[0].StaCount==1);
setup(&a,&one);MacTableReset(&a,1);assert(!a.MacTab.Size&&a.ApCfg.MBSSID[0].StaCount==0);
setup(&a,&one);a.MacTab.tr_entry[1]=(STA_TR_ENTRY){1,0};mac=1;
assert(ordinary_delete(&a,&a.MacTab.tr_entry[1])&&mac);mac=0;
return 0;}
'''
if checked:
 replacements={
  'MacTableReset(&a,1);assert(!released':'assert(!MacTableReset(&a,1));assert(!released',
  'MacTableResetWdev(&a,&one);assert(!released':'assert(!MacTableResetWdev(&a,&one));assert(!released',
  'MacTableResetWdev(&a,&two);assert(!released':'assert(MacTableResetWdev(&a,&two));assert(!released',
  'delete_ok=0;MacTableReset(&a,1);':'delete_ok=0;assert(!MacTableReset(&a,1));',
  'delete_ok=0;MacTableResetWdev(&a,&one);':'delete_ok=0;assert(!MacTableResetWdev(&a,&one));',
  'setup(&a,&one);MacTableReset(&a,1);assert(!a.MacTab.Size':'setup(&a,&one);assert(MacTableReset(&a,1));assert(!a.MacTab.Size',
 }
 for old,new in replacements.items():
  assert suffix.count(old)==1,old
  suffix=suffix.replace(old,new,1)
 extra='''
setup(&a,&one);a.MacTab.Content[1].Sst=SST_ASSOC;alloc_fail=1;
assert(!MacTableReset(&a,1)&&released==1&&!deleted&&a.MacTab.Size==1);
setup(&a,&one);a.MacTab.Content[1].Sst=SST_ASSOC;alloc_fail=1;
assert(!MacTableResetWdev(&a,&one)&&released==1&&!deleted&&a.MacTab.Size==1);
alloc_fail=0;setup(&a,&one);assert(MacTableResetWdev(&a,&one)&&!a.MacTab.Size);
'''
 suffix=suffix.replace('return 0;}\n',extra+'return 0;}\n',1)
owned='wr_iot_peer_reset_begin(' in functions
if owned:
 prefix='#include "peer-table-owner.h"\n'+prefix
 prefix=prefix.replace('unsigned int wr_iot_peer_delete_active;MAC_TABLE MacTab;',
  'unsigned int wr_iot_peer_delete_active;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;MAC_TABLE MacTab;')
 prefix=prefix.replace('static BOOLEAN MacTableDeleteEntry(RTMP_ADAPTER *a,int i,UCHAR *addr){',
 '''static BOOLEAN wr_iot_mac_delete_entry(RTMP_ADAPTER *a,int i,UCHAR *addr,
 const void *device,unsigned long generation,unsigned long token,unsigned long serial){
 (void)device;(void)generation;(void)token;
 assert(!mac&&!irq&&wr_iot_peer_table_allows(&a->wr_iot_peer_table_owner,serial));
 assert(!wr_iot_peer_table_allows(&a->wr_iot_peer_table_owner,0));''')
 prefix=prefix.replace('#include "wr-iot-peer-failed-reset-preflight.inc"',
 '#include "wr-iot-peer-table-reset-owner.inc"')
 prefix=prefix.replace('static BOOLEAN wr_iot_mac_delete_entry(',
 '''BOOLEAN MacTableReset(RTMP_ADAPTER *pAd,INT startWcid);
static int nested_attempt;
static BOOLEAN wr_iot_mac_delete_entry(''',1)
 prefix=prefix.replace('(void)addr;deleted++;if(!delete_ok)return FALSE;',
 '''(void)addr;
 if(nested_attempt){nested_attempt=0;assert(!MacTableReset(a,1));
  assert(wr_iot_peer_table_allows(&a->wr_iot_peer_table_owner,serial));}
 deleted++;if(!delete_ok)return FALSE;''')
 extra=r'''
setup(&a,&one);assert(MacTableReset(&a,1)&&!a.wr_iot_peer_table_owner.active&&!mac&&!irq);
assert(MacTableReset(&a,1)&&a.wr_iot_peer_table_owner.serial==2);
setup(&a,&one);nested_attempt=1;assert(MacTableReset(&a,1)&&!nested_attempt&&!mac&&!irq);
setup(&a,&one);delete_ok=0;assert(!MacTableReset(&a,1));
assert(a.wr_iot_peer_table_owner.active&&a.wr_iot_peer_table_owner.retained&&!mac&&!irq);
{int before=deleted;delete_ok=1;assert(!MacTableReset(&a,1)&&deleted==before);}
setup(&a,&one);a.MacTab.Content[1].Sst=SST_ASSOC;alloc_fail=1;
assert(!MacTableResetWdev(&a,&one)&&a.wr_iot_peer_table_owner.retained&&!mac&&!irq);
alloc_fail=0;assert(!MacTableResetWdev(&a,&one)&&a.wr_iot_peer_table_owner.retained);
'''
 suffix=suffix.replace('return 0;}\n',extra+'return 0;}\n',1)
a.output.write_text(prefix+functions+suffix,encoding='utf-8')
print('Extracted whole reset '+('owner/retention' if owned else 'refusal')+' flow; kernel concurrency and lifetime unproved')
