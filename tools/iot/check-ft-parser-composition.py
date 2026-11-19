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
assert request.index(check)<request.index('MacTableLookup')<request.index('FT_AuthReqHandler')
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
 subprocess.run(['gcc','-std=gnu11','-O2',str(src),'-o',str(exe)],check=True)
 def no_core():resource.setrlimit(resource.RLIMIT_CORE,(0,0))
 result=subprocess.run([str(exe)],capture_output=True,text=True,preexec_fn=no_core)
 assert result.returncode!=0 and 'queued_wcid==7' in result.stderr,result.stderr
print('PASS | original MAC-only producer rejected by same cross-BSS regression assertions')
