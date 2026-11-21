#!/usr/bin/env python3
"""Check bounded FT parsing is scoped to terminating request/confirm branches."""
import argparse,runpy
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
native=(a.source/'common/ft.c').read_text()
compose=runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose']
text=compose(native);start=text.index('VOID FT_FtAction(');body=text[start:text.index('\n}',start)+2]
check='if(!wr_iot_ft_request_ies_admitted(pFtAction->Oct,wr_ie_length))goto out;'
assert body.count(check)==2
assert body.index('wr_iot_ft_action_payload_length')<body.index('os_alloc_mem')
assert 'wr_iot_ft_request_ies_admitted' not in body[:body.index('switch(pFtAction->Action)')]
request=body[body.index('case FT_ACTION_BT_REQ:'):body.index('case FT_ACTION_BT_CONFIRM:')]
assert request.index(check)<request.index('NdisAcquireSpinLock')<request.index('FT_AuthReqHandler')
assert 'MacTableLookup' not in request
confirm=body[body.index('case FT_ACTION_BT_CONFIRM:'):]
assert confirm.index(check)<confirm.index('if (Elem->Wcid < MAX_LEN_OF_MAC_TABLE)')<confirm.index('FT_AuthConfirmHandler')
# Both forwarding call sites remain byte-identical; they are outside the
# terminating branches guarded above. No generic TLV check before the switch.
for fragment in (
 'FT_RrbEnqueue(pAd, pFtAction->TargetApAddr,\n\t\t\t\t\t\t\t(PFT_ACTION)pFtAction, FtActLen, apidx);',):
 assert native.count(fragment)==text.count(fragment)>0
assert 'sizeof(PFT_ACTION)' not in body
assert request.index('if(!pEntry)goto out;')>request.index('MacTableInsertEntry')
assert request.index('if(!pEntry)goto out;')<request.index('FT_ReqActionParse')
assert 'if (pEntry->func_tb_idx >= pAd->ApCfg.BssidNum)' in confirm
assert 'if (pEntry->func_tb_idx > pAd->ApCfg.BssidNum)' not in confirm
try:compose(text)
except ValueError:pass
else:raise AssertionError('duplicate accepted')
print('FT bounds composition: outer admission, terminating request/confirm validation before lookup, native forwarding preserved PASS')

# Execute the composed producer's pre-allocation selection, including native
# declarations. Native allocation/frame construction/MLME are outside this test.
import subprocess,tempfile
start=text.index('VOID FT_RrbHandler(')
rrb=text[start:text.index('\n}',start)+2]
assert 'MacTableLookup' not in rrb
assert rrb.index('if(Wcid==RESERVED_WCID)return;')<rrb.index('MlmeAllocateMemory')<rrb.index('REPORT_MGMT_FRAME_TO_MLME')
prefix=rrb[rrb.index('{')+1:rrb.index('\tStatus = MlmeAllocateMemory')]
prefix=prefix.replace('return;','return -1;')
code=r'''
#include <assert.h>
#include <stddef.h>
#include <string.h>
typedef unsigned char *PUCHAR;
typedef unsigned long ULONG;
typedef int INT32;
typedef int INT;
typedef int NDIS_STATUS;
typedef struct {unsigned char bytes[24];} HEADER_802_11;
typedef struct {unsigned char type,packet;unsigned short FTActLen;unsigned char APAdr[6],Oct[0];} FT_RRB,*PFT_RRB;
typedef struct {unsigned char category,action,StaMac[6],TargetApAddr[6],Oct[0];} FT_ACTION,*PFT_ACTION;
struct wifi_dev {int id;};
typedef struct {unsigned int wcid;int func_tb_idx,Sst,client;unsigned char Addr[6];struct wifi_dev *wdev;} ENTRY,*PMAC_TABLE_ENTRY;
typedef struct {int MacTabLock;struct {int BssidNum;struct {struct wifi_dev wdev;} MBSSID[3];} ApCfg;struct {ENTRY Content[8];} MacTab;} AD,*PRTMP_ADAPTER;
#define LENGTH_802_3 14
#define MGMT_DMA_BUFFER_SIZE 1600
#define MAX_LEN_OF_MAC_TABLE 8
#define RESERVED_WCID 0
#define SST_AUTH 1
#define SST_ASSOC 2
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define MAC_ADDR_EQUAL(a,b) (!memcmp(a,b,6))
#define NdisAcquireSpinLock(p) assert(!(*(p))++)
#define NdisReleaseSpinLock(p) assert(--(*(p))==0)
static int get_apidx_by_addr(AD *ad,unsigned char *addr){(void)ad;return addr[0];}
static int select_slot(AD *pAd,PUCHAR pPktSrc,INT32 PktLen){
'''+prefix+r'''
return Wcid;
}
int main(void){
 AD ad={0};unsigned char packet[38]={2};
 FT_RRB *r=(FT_RRB*)(packet+14);FT_ACTION *act=(FT_ACTION*)r->Oct;
 ad.ApCfg.BssidNum=3;r->FTActLen=14;act->StaMac[0]=42;
 ENTRY *wrong=&ad.MacTab.Content[3],*right=&ad.MacTab.Content[7];
 *wrong=(ENTRY){.wcid=3,.func_tb_idx=0,.Sst=SST_ASSOC,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[0].wdev};
 *right=(ENTRY){.wcid=7,.func_tb_idx=2,.Sst=SST_ASSOC,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 assert(select_slot(&ad,packet,38)==7); /* Earlier same MAC, unrelated BSS. */
 wrong->client=0;assert(select_slot(&ad,packet,38)==7);
 right->Sst=SST_AUTH;assert(select_slot(&ad,packet,38)==7);right->Sst=SST_ASSOC;
 right->Sst=0;assert(select_slot(&ad,packet,38)==-1);right->Sst=SST_ASSOC;
 right->wdev=wrong->wdev;assert(select_slot(&ad,packet,38)==-1);right->wdev=&ad.ApCfg.MBSSID[2].wdev;
 right->func_tb_idx=1;assert(select_slot(&ad,packet,38)==-1);right->func_tb_idx=2;
 right->wcid=6;assert(select_slot(&ad,packet,38)==-1);right->wcid=7;
 right->Addr[0]=43;assert(select_slot(&ad,packet,38)==-1);right->Addr[0]=42;
 right->client=0;assert(select_slot(&ad,packet,38)==-1);right->client=1;
 for(int n=-1;n<38;n++)assert(select_slot(&ad,packet,n)==-1);
 r->FTActLen=15;assert(select_slot(&ad,packet,38)==-1);r->FTActLen=14;
 packet[0]=3;assert(select_slot(&ad,packet,38)==-1);
 assert(select_slot(&ad,0,38)==-1);assert(select_slot(0,packet,38)==-1);
 assert(ad.MacTabLock==0);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-rrb-context-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS | composed RRB selection | active client, MAC/BSS/wdev/WCID, absent-context refusal before enqueue, truncated lengths')

# Run the entire composed RRB handler with explicit allocation, framing and
# queue actors; this verifies actual call ordering and queue suppression.
base=code[:code.index('static int select_slot(')]
actors=r'''
#include <stdlib.h>
#include <stdarg.h>
#define IN
#define VOID void
#define NDIS_STATUS_SUCCESS 0
#define END_OF_ARGS -1
#define DBGPRINT(level,args) ((void)0)
static int allocated,freed,enqueued,fail_alloc;
static ULONG queued_wcid,queued_length;
static int MlmeAllocateMemory(AD *ad,PUCHAR *out){
 (void)ad;if(fail_alloc)return 1;*out=malloc(MGMT_DMA_BUFFER_SIZE);
 assert(*out);allocated++;return 0;
}
static void os_free_mem(AD *ad,PUCHAR p){(void)ad;assert(p);freed++;free(p);}
static void ActHeaderInit(AD *ad,HEADER_802_11 *hdr,PUCHAR da,PUCHAR sa,PUCHAR ap){
 (void)ad;(void)da;(void)sa;(void)ap;memset(hdr,0,sizeof(*hdr));
}
static void MakeOutgoingFrame(PUCHAR out,ULONG *length,int hlen,HEADER_802_11 *hdr,...){
 va_list args;va_start(args,hdr);int len=va_arg(args,int);PUCHAR body=va_arg(args,PUCHAR);
 assert(va_arg(args,int)==END_OF_ARGS);va_end(args);
 assert(hlen+len<=MGMT_DMA_BUFFER_SIZE);memcpy(out,hdr,hlen);memcpy(out+hlen,body,len);
 *length=hlen+len;
}
#define REPORT_MGMT_FRAME_TO_MLME(ad,wcid,buffer,length,a,b,c,d,e) do { \
 assert(!(ad)->MacTabLock);assert(buffer);enqueued++;queued_wcid=(wcid);queued_length=(length); \
}while(0)
'''
main=r'''
int main(void){
 AD ad={0};ad.ApCfg.BssidNum=3;
 ENTRY *wrong=&ad.MacTab.Content[3],*right=&ad.MacTab.Content[7];
 *wrong=(ENTRY){.wcid=3,.func_tb_idx=0,.Sst=SST_ASSOC,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[0].wdev};
 *right=(ENTRY){.wcid=7,.func_tb_idx=2,.Sst=SST_ASSOC,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 unsigned char *packet=calloc(1,38);assert(packet);packet[0]=2;
 FT_RRB *r=(FT_RRB*)(packet+14);r->FTActLen=14;((FT_ACTION*)r->Oct)->StaMac[0]=42;
 FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&queued_wcid==7&&queued_length==38);
 assert(allocated==1&&freed==1);
 right->Sst=SST_AUTH;FT_RrbHandler(&ad,packet,38);
 assert(enqueued==2&&allocated==2&&freed==2);
 /* Reset actor counts to reuse the same rejection assertions below. */
 enqueued=allocated=freed=1;right->Sst=SST_ASSOC;
 right->Sst=0;FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1);right->Sst=SST_ASSOC;
 right->wdev=wrong->wdev;FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1);
 right->wdev=&ad.ApCfg.MBSSID[2].wdev;right->client=0;
 FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1);right->client=1;
 fail_alloc=1;FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1&&freed==1);fail_alloc=0;
 for(int n=0;n<38;n++){
  unsigned char *short_packet=calloc(1,n?n:1);assert(short_packet);
  memcpy(short_packet,packet,n);FT_RrbHandler(&ad,short_packet,n);free(short_packet);
 }
 FT_RrbHandler(&ad,0,38);FT_RrbHandler(0,packet,38);FT_RrbHandler(&ad,packet,-1);
 r->FTActLen=15;FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1);free(packet);
 /* Exact output capacity admitted; one more input byte refused before allocation. */
 for(int excess=0;excess<2;excess++){
  int action=MGMT_DMA_BUFFER_SIZE-sizeof(HEADER_802_11)+excess;
  int size=14+offsetof(FT_RRB,Oct)+action;packet=calloc(1,size);assert(packet);packet[0]=2;
  r=(FT_RRB*)(packet+14);r->FTActLen=action;((FT_ACTION*)r->Oct)->StaMac[0]=42;
  FT_RrbHandler(&ad,packet,size);free(packet);
 }
 assert(enqueued==2&&allocated==2&&freed==2&&queued_length==MGMT_DMA_BUFFER_SIZE);
 assert(ad.MacTabLock==0);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-rrb-handler-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(base+actors+rrb+main)
 subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS | complete composed RRB handler | context refusal suppresses allocation/enqueue, valid WCID, allocation failure, exact input/output capacities')

# The same behavioral assertions must reject the original MAC-only producer.
# Disable core dumps for this expected assertion failure.
import resource
native_start=native.index('VOID FT_RrbHandler(')
native_rrb=native[native_start:native.index('\n}',native_start)+2]
lookup=r'''
static ENTRY *MacTableLookup(AD *ad,PUCHAR addr){
 for(int i=1;i<8;i++)if(ad->MacTab.Content[i].client&&MAC_ADDR_EQUAL(ad->MacTab.Content[i].Addr,addr))return &ad->MacTab.Content[i];
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-rrb-original-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(base+actors+lookup+native_rrb+main)
 subprocess.run(['gcc','-std=gnu11','-O2','-I'+str(here),str(src),'-o',str(exe)],check=True)
 def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 result=subprocess.run([str(exe)],capture_output=True,text=True,preexec_fn=no_core)
 assert result.returncode!=0 and 'queued_wcid==7' in result.stderr,result.stderr
print('PASS | original MAC-only producer rejected by same cross-BSS regression assertions')

# Execute full native action control flow, using handler/crypto/transport actors.
action_prefix=r'''
#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#define IN
#define VOID void
#define TRUE 1
#define FALSE 0
#define LENGTH_802_11 24
#define MAX_LEN_OF_MAC_TABLE 8
#define RESERVED_WCID 0
#define SST_AUTH 1
#define SST_ASSOC 2
#define AS_AUTH_OPEN 1
#define ENTRY_CLIENT 1
#define OPMODE_AP 1
#define MLME_SUCCESS 0
#define NDIS_STATUS_SUCCESS 0
#define FT_ACTION_BT_REQ 1
#define FT_ACTION_BT_RSP 2
#define FT_ACTION_BT_CONFIRM 3
#define FT_ACTION_BT_ACK 4
#define END_OF_ARGS -1
#define DBGPRINT(level,args) ((void)0)
#define MAC_ADDR_EQUAL(a,b) (!memcmp(a,b,6))
#define COPY_MAC_ADDR(a,b) memcpy(a,b,6)
#define NdisZeroMemory(a,n) memset(a,0,n)
#define NdisMoveMemory memcpy
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define NdisAcquireSpinLock(p) assert(!(*(p))++)
#define NdisReleaseSpinLock(p) assert(--(*(p))==0)
typedef unsigned char UCHAR,*PUCHAR;
typedef unsigned short UINT16,USHORT;
typedef unsigned long ULONG;
typedef int INT,BOOLEAN,NDIS_STATUS;
typedef struct {unsigned char Addr1[6],Addr2[6],Addr3[6];struct {unsigned char ToDs,FrDs;} FC;unsigned char pad[4];} HEADER_802_11,*PHEADER_802_11;
typedef struct __attribute__((packed)){unsigned char Category,Action,StaMac[6],TargetApAddr[6],Oct[0];} FT_ACTION,*PFT_ACTION;
typedef int FT_MDIE_INFO;
typedef struct {int MdIeInfo;struct {PUCHAR pRicInfo;} RicInfo;} FT_INFO,*PFT_INFO;
typedef struct {struct {int Dot11rFtEnable;} FtCapFlag;} FT_CFG,*PFT_CFG;
struct wifi_dev{unsigned char bssid[6];};
typedef struct {unsigned wcid;int client,func_tb_idx,Sst,AuthState,MdIeInfo;unsigned char Addr[6];struct wifi_dev *wdev;} ENTRY,*PMAC_TABLE_ENTRY;
typedef struct {int MacTabLock;struct {int BssidNum;struct {struct wifi_dev wdev;FT_CFG FtCfg;} MBSSID[3];} ApCfg;struct {ENTRY Content[8];} MacTab;} AD,*PRTMP_ADAPTER;
typedef struct {ULONG MsgLen;unsigned Wcid;unsigned char Msg[256];} MLME_QUEUE_ELEM;
#include "ft-action-bounds.h"
/* Parser admission is an explicit actor here; real parser checked separately. */
static int wr_iot_ft_request_ies_admitted(PUCHAR ptr,unsigned len){(void)ptr;return len==0;}
static int allocs,frees,reqs,confirms,forwards,inserted,fail_insert;
static int get_apidx_by_addr(AD *ad,PUCHAR addr){(void)ad;return addr[0];}
static int os_alloc_mem(AD *ad,PUCHAR *out,unsigned n){(void)ad;*out=calloc(1,n);assert(*out);allocs++;return 0;}
static void os_free_mem(AD *ad,void *out){(void)ad;assert(out);free(out);frees++;}
#define MlmeAllocateMemory(ad,out) os_alloc_mem(ad,out,256)
#define MlmeFreeMemory(ad,out) os_free_mem(ad,out)
static ENTRY *MacTableInsertEntry(AD *ad,PUCHAR mac,struct wifi_dev *w,int type,int mode,int yes){
 (void)type;(void)mode;(void)yes;assert(!ad->MacTabLock);inserted++;if(fail_insert)return NULL;
 ENTRY *e=&ad->MacTab.Content[7];*e=(ENTRY){.wcid=7,.client=1,.func_tb_idx=2,.wdev=w};memcpy(e->Addr,mac,6);return e;
}
static void FT_ReqActionParse(AD *ad,UINT16 len,PUCHAR ptr,FT_INFO *info){(void)ad;(void)len;(void)ptr;info->MdIeInfo=123;}
static int FT_AuthReqHandler(AD *ad,ENTRY *e,FT_INFO *in,FT_INFO *out){(void)in;(void)out;assert(!ad->MacTabLock);assert(e->func_tb_idx==2);reqs++;return MLME_SUCCESS;}
static int FT_AuthConfirmHandler(AD *ad,ENTRY *e,FT_INFO *in,FT_INFO *out){(void)in;(void)out;assert(!ad->MacTabLock);assert(e->func_tb_idx==2);confirms++;return MLME_SUCCESS;}
#define FT_MakeFtActFrame(...) ((void)0)
#define FT_RrbEnqueue(...) (++forwards)
#define MakeOutgoingFrame(...) ((void)0)
#define MiniportMMRequest(...) (++forwards)
'''
action_main=r'''
int main(void){
 AD ad={0};ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.bssid[0]=2;
 ad.ApCfg.MBSSID[2].FtCfg.FtCapFlag.Dot11rFtEnable=1;
 MLME_QUEUE_ELEM event={.MsgLen=38,.Wcid=7};
 HEADER_802_11 *hdr=(void*)event.Msg;hdr->Addr1[0]=2;hdr->Addr2[0]=42;
 FT_ACTION *act=(void*)(event.Msg+24);act->Action=FT_ACTION_BT_REQ;act->StaMac[0]=42;act->TargetApAddr[0]=2;
 ENTRY *right=&ad.MacTab.Content[7],*wrong=&ad.MacTab.Content[3];
 *right=(ENTRY){.wcid=7,.client=1,.func_tb_idx=2,.Sst=SST_ASSOC,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 *wrong=(ENTRY){.wcid=3,.client=1,.func_tb_idx=0,.Sst=SST_ASSOC,.Addr={42},.wdev=&ad.ApCfg.MBSSID[0].wdev};
 FT_FtAction(&ad,&event);assert(reqs==1&&!inserted&&right->Sst==SST_AUTH&&wrong->Sst==SST_ASSOC);
 act->Action=FT_ACTION_BT_CONFIRM;FT_FtAction(&ad,&event);assert(confirms==1);
 event.Wcid=3;FT_FtAction(&ad,&event);assert(confirms==1);
 event.Wcid=0;FT_FtAction(&ad,&event);assert(confirms==1);
 event.Wcid=8;FT_FtAction(&ad,&event);assert(confirms==1);event.Wcid=7;
 for(int fault=0;fault<6;fault++){
  ENTRY saved=*right;
  if(fault==0)right->client=0;if(fault==1)right->func_tb_idx=0;
  if(fault==2)right->wdev=wrong->wdev;if(fault==3)right->Sst=0;
  if(fault==4)right->Addr[0]=43;if(fault==5)right->wcid=6;
  FT_FtAction(&ad,&event);assert(confirms==1);*right=saved;
 }
 act->StaMac[0]=43;FT_FtAction(&ad,&event);assert(confirms==1);
 act->Action=FT_ACTION_BT_REQ;FT_FtAction(&ad,&event);assert(reqs==1&&!inserted);act->StaMac[0]=42;
 right->client=0;fail_insert=1;FT_FtAction(&ad,&event);assert(reqs==1&&inserted==1);
 fail_insert=0;FT_FtAction(&ad,&event);assert(reqs==2&&inserted==2&&right->Sst==SST_AUTH);
 for(int len=0;len<38;len++){event.MsgLen=len;FT_FtAction(&ad,&event);}assert(reqs==2);event.MsgLen=38;
 int sent=forwards;act->TargetApAddr[0]=1;FT_FtAction(&ad,&event);assert(forwards==sent+1&&reqs==2);
 assert(allocs==frees&&!ad.MacTabLock);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-action-context-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(action_prefix+body+action_main)
 subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS | complete composed FT action | BSS/wdev/MAC/WCID refusal, request-to-confirm state, insertion refusal/success, forwarding, balanced frees')
# The original action's same-MAC lookup must fail this cross-BSS scenario.
native_at=native.index('VOID FT_FtAction(')
native_action=native[native_at:native.index('\n}',native_at)+2]
with tempfile.TemporaryDirectory(prefix='wr-ft-action-original-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(action_prefix+lookup+native_action+action_main)
 subprocess.run(['gcc','-std=gnu11','-O2','-I'+str(here),str(src),'-o',str(exe)],check=True)
 result=subprocess.run([str(exe)],capture_output=True,text=True,preexec_fn=no_core)
 assert result.returncode!=0 and (
  'e->func_tb_idx==2' in result.stderr or
  'reqs==1&&!inserted&&right->Sst==SST_AUTH&&wrong->Sst==SST_ASSOC' in result.stderr),result.stderr
print('PASS | original FT action rejected by same cross-BSS/state assertions')

# Compile the real existing-peer identity/lease primitive; no queue or crypto actors.
with tempfile.TemporaryDirectory(prefix='wr-ft-peer-generation-') as td:
 exe=Path(td)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror',
  '-Wno-misleading-indentation','-O2','-fsanitize=address,undefined',
  '-fno-pie','-no-pie','-I'+str(here),str(here/'check-ft-peer-generation.c'),
  '-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS | FT peer generation primitive | immutable capture, stale/BSS/state refusal, linear lease, reset exclusion, uncertain ownership retained')
