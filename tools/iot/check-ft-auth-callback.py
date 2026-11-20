#!/usr/bin/env python3
"""Execute composed native over-air FT branch with real existing-peer scope."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--request-context',action='store_true');a=p.parse_args();here=Path(__file__).resolve().parent
argv=sys.argv[:];sys.argv=[str(here/'check-ft-auth-rx-queue.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):data=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
native=(a.source/'ap/ap_auth.c').read_text()
composed=runpy.run_path(str(here/'ft-auth-callback-composition.py'))['compose'](native)
if a.request_context:
 composed=runpy.run_path(str(here/'ft-auth-request-context-composition.py'))['compose_callback'](composed)
start=composed.index('\tpFtCfg = &pMbss->FtCfg;');end=composed.index('\n\telse\n#endif /* DOT11R_FT_SUPPORT */',start)
branch=composed[start:end]
prefix=data['prefix'].replace('struct wifi_dev{unsigned char bssid[6];};',
 'struct wifi_dev{unsigned char bssid[6];unsigned func_idx;};')
prefix=prefix.replace('typedef unsigned char UCHAR;', '''typedef unsigned char UCHAR;
typedef unsigned short USHORT;
typedef struct {unsigned char value[8];} FT_MDIE_INFO;
typedef struct {FT_MDIE_INFO MdIeInfo;int FtIeInfo;unsigned char RSN_IE[64];int RSNIE_Len;} FT_INFO;
typedef struct {struct {int Dot11rFtEnable;} FtCapFlag;} FT_CFG,*PFT_CFG;
''')
prefix=prefix.replace('struct {struct wifi_dev wdev;} MBSSID[3]', 'struct {struct wifi_dev wdev;FT_CFG FtCfg;} MBSSID[3]')
prefix=prefix.replace('unsigned assoc_gen,wcid,func_tb_idx;int Sst,client;',
 'FT_MDIE_INFO MdIeInfo;unsigned char LastTK[16];int AuthState,FT_R1kh_CacheMiss_Times;unsigned assoc_gen,wcid,func_tb_idx;int Sst,client;')
# This fixture tests existing-peer branch; absent-peer integration has separate gates.
actors=r'''
#define MLME_SUCCESS 0
#define MLME_FAIL_NO_RESOURCE 1
#define AUTH_MODE_FT 2
#define AS_AUTH_OPEN 1
#define SST_NOT_AUTH 0
#define LEN_TK 16
#define CATPROTO_FT 0
#define MTWF_LOG(a,b,c,args) ((void)0)
#include "peer-close-executor.h"
#include "ft-pending-peer-scope.h"
#include "ft-iapp-pending-admission.h"
static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){
 ad->wr_assoc_visible[entry->wcid]=entry->assoc_gen;
 memcpy(ad->wr_assoc_addr[entry->wcid],entry->Addr,6);
}
static int allocation_fail,allocations,frees,auth_calls,auth_result,replies,failures;
static int os_alloc_mem(RTMP_ADAPTER *ad,UCHAR **out,size_t n){(void)ad;*out=NULL;if(allocation_fail)return 1;*out=calloc(1,n);assert(*out);allocations++;return 0;}
static void os_free_mem(void *ad,void *p){(void)ad;assert(p);free(p);frees++;}
static USHORT FT_AuthReqHandler(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry,FT_INFO *in,FT_INFO *out){
 (void)in;(void)out;assert(entry->Sst==SST_NOT_AUTH||entry->Sst==SST_ASSOC);assert(ad->wr_assoc_event_users[entry->wcid]==1);assert(ad->wr_iot_peer_table_owner.transactions==1);auth_calls++;return auth_result;
}
static void FT_EnqueueAuthReply(RTMP_ADAPTER *ad,...){
 MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[7];
 assert(ad->wr_assoc_event_users[7]==1&&ad->wr_iot_peer_table_owner.transactions==1);
 assert(!ad->MacTabLock);
 assert(entry->assoc_gen==(auth_result==MLME_SUCCESS?2:1));
 replies++;
}
static MAC_TABLE_ENTRY *wr_ft_pending_insert(RTMP_ADAPTER *ad,UCHAR *mac,struct wifi_dev *wdev,const struct wr_ft_pending_token *ticket,struct wr_ft_pending_peer_scope *scope){
 MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[7];
 NdisAcquireSpinLock(&ad->MacTabLock);
 assert(wr_ft_pending_claim_locked(&ad->wr_ft_pending,ticket));
 assert(wr_ft_pending_peer_reserve_slot_locked(ad,7,wdev,ticket,scope));
 memset(entry,0,sizeof(*entry));entry->wcid=7;entry->client=1;
 entry->Sst=SST_NOT_AUTH;entry->func_tb_idx=ticket->bss;entry->wdev=wdev;memcpy(entry->Addr,mac,6);
 entry->assoc_gen=wr_assoc_generation_next(&ad->wr_assoc_generations[7]);
 wr_assoc_publish_slot_locked(ad,entry);
 assert(wr_ft_pending_peer_publish_locked(ad,entry,ticket,scope));
 assert(wr_ft_iapp_pending_owned_locked(ad,scope));
 {
 struct wr_ft_iapp_token_ledger ledger;
 struct wr_ft_iapp_token_handle request={0},response={0};
 unsigned char token[7]={1,2,3,4,5,6,7};
 wr_ft_iapp_token_ledger_init(&ledger);
 assert(wr_ft_iapp_pending_request_begin_locked(ad,&ledger,token,scope,&request));
 entry->assoc_gen++;
 assert(!wr_ft_iapp_pending_admit_locked(ad,&ledger,token,mac,wdev->bssid,scope,&request,&response));
 entry->assoc_gen--;
 assert(wr_ft_iapp_pending_admit_locked(ad,&ledger,token,mac,wdev->bssid,scope,&request,&response));
 assert(!wr_ft_iapp_pending_request_end_locked(ad,scope,&ledger,&request));
 assert(scope->active&&ad->wr_assoc_event_users[7]==1&&request.serial);
 assert(wr_ft_iapp_token_finish_locked(&ledger,&response));
 assert(wr_ft_iapp_pending_request_end_locked(ad,scope,&ledger,&request));
 token[0]=9;
 assert(wr_ft_iapp_pending_request_begin_locked(ad,&ledger,token,scope,&request));
 assert(wr_ft_iapp_pending_request_end_locked(ad,scope,&ledger,&request));
 assert(!request.serial);
 assert(!wr_ft_iapp_token_claim_locked(&ledger,token,mac,wdev->bssid,&response));
 assert(ad->wr_assoc_event_users[7]==1);
 }

 entry->wdev=&ad->ApCfg.MBSSID[0].wdev;
 assert(!wr_ft_iapp_pending_owned_locked(ad,scope));entry->wdev=wdev;
 ad->wr_assoc_visible[7]=0;
 assert(!wr_ft_iapp_pending_owned_locked(ad,scope));
 ad->wr_assoc_visible[7]=entry->assoc_gen;
 assert(wr_ft_iapp_pending_owned_locked(ad,scope));
 assert(wr_ft_pending_retire_key_locked(&ad->wr_ft_pending,ticket->bss,mac)==1);
 NdisReleaseSpinLock(&ad->MacTabLock);return entry;
}
static void callback(RTMP_ADAPTER *pAd,MLME_QUEUE_ELEM *Elem){
 unsigned apidx=2;MAC_TABLE_ENTRY *pEntry=NULL;struct wifi_dev *wdev=&pAd->ApCfg.MBSSID[2].wdev;
 __typeof__(pAd->ApCfg.MBSSID[0]) *pMbss=&pAd->ApCfg.MBSSID[2];
 PFT_CFG pFtCfg;FT_INFO *pFtInfoBuf=NULL;void *pRcvHdr=Elem->Msg;
 struct {unsigned char addr2[6];unsigned auth_alg;FT_INFO FtInfo;} auth_info={.auth_alg=AUTH_MODE_FT};
 memcpy(auth_info.addr2,((FRAME_802_11 *)Elem->Msg)->Hdr.Addr2,6);
'''+branch+r'''
 return;
auth_failure:failures++;
}
'''
if a.request_context:
 actors=actors.replace('#include "ft-iapp-pending-admission.h"',
  '#include "ft-iapp-pending-admission.h"\n#include "ft-auth-request-context.h"\nstatic int exhaust_generation;')
 actors=actors.replace('FT_INFO *in,FT_INFO *out){',
  'FT_INFO *in,FT_INFO *out,const struct wr_ft_auth_request_context *context){')
 actors=actors.replace(' (void)in;(void)out;',r'''
 struct wr_ft_auth_request_context empty={0},bad;
 struct wr_ft_peer_scope existing={0};struct wr_ft_pending_peer_scope pending={0};
 NdisAcquireSpinLock(&ad->MacTabLock);
 assert(wr_ft_auth_request_current_locked(ad,entry,context));
 assert(!wr_ft_auth_request_current_locked(ad,entry,NULL));
 assert(!wr_ft_auth_request_current_locked(ad,entry,&empty));
 assert(!wr_ft_auth_request_current_locked(ad,&ad->MacTab.Content[1],context));
 if(context->existing->active){
  existing=*context->existing;bad=(struct wr_ft_auth_request_context){&existing,&pending};
  existing.stamp.generation++;
  assert(!wr_ft_auth_request_current_locked(ad,entry,&bad));
  existing=*context->existing;existing.adapter=NULL;
  assert(!wr_ft_auth_request_current_locked(ad,entry,&bad));
 }else{
  pending=*context->pending;bad=(struct wr_ft_auth_request_context){&existing,&pending};
  pending.generation++;
  assert(!wr_ft_auth_request_current_locked(ad,entry,&bad));
  pending=*context->pending;pending.adapter=NULL;
  assert(!wr_ft_auth_request_current_locked(ad,entry,&bad));
 }
 existing.active=pending.active=1;bad=(struct wr_ft_auth_request_context){&existing,&pending};
 assert(!wr_ft_auth_request_current_locked(ad,entry,&bad));
 NdisReleaseSpinLock(&ad->MacTabLock);
 if(exhaust_generation)ad->wr_assoc_generations[entry->wcid]=~0U;
 (void)in;(void)out;''',1)
main=r'''
int main(void){
 for(int scenario=0;scenario<8;scenario++){
 RTMP_ADAPTER ad={0};MLME_QUEUE_ELEM event={0};
 ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.bssid[0]=2;ad.ApCfg.MBSSID[2].FtCfg.FtCapFlag.Dot11rFtEnable=1;
 MAC_TABLE_ENTRY *e=&ad.MacTab.Content[7];*e=(MAC_TABLE_ENTRY){.assoc_gen=1,.wcid=7,.func_tb_idx=2,.Sst=SST_ASSOC,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 ad.wr_assoc_generations[7]=ad.wr_assoc_visible[7]=1;ad.wr_assoc_addr[7][0]=42;
 event.assoc_gen=1;event.assoc_wcid=event.Wcid=7;event.assoc_addr[0]=42;
 event.Machine=AP_AUTH_STATE_MACHINE;event.MsgType=APMT2_PEER_AUTH_REQ;event.MsgLen=30;
 FRAME_802_11 *frame=(FRAME_802_11 *)event.Msg;frame->Hdr.FC.Type=FC_TYPE_MGMT;frame->Hdr.FC.SubType=SUBTYPE_AUTH;
 frame->Hdr.Addr1[0]=2;frame->Hdr.Addr2[0]=42;event.Msg[24]=2;event.Msg[26]=1;
 if(scenario==3)ad.wr_assoc_generations[7]=~0U;
 if(scenario>=5){
  struct wr_ft_pending_token ticket={0};
  memset(e,0,sizeof(*e));ad.wr_assoc_generations[7]=ad.wr_assoc_visible[7]=0;
  ad.ApCfg.MBSSID[2].wdev.func_idx=2;
  wr_ft_pending_ledger_init(&ad.wr_ft_pending);
  event.assoc_gen=event.assoc_wcid=event.Wcid=0;
  assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,frame->Hdr.Addr2,&ticket));
  assert(wr_ft_pending_elem_publish(&event,&ticket));
 }
 allocation_fail=(scenario==2||scenario==7);auth_result=(scenario==1||scenario==6)?MLME_FAIL_NO_RESOURCE:(scenario==4?55:MLME_SUCCESS);
 auth_calls=replies=failures=allocations=frees=0;
 callback(&ad,&event);
 if(scenario==3){
  assert(ad.wr_iot_peer_table_owner.poisoned);
  assert(ad.wr_assoc_event_users[7]==1&&ad.wr_iot_peer_table_owner.transactions==1);
  assert(!ad.MacTabLock&&allocations==frees&&e->assoc_gen==1&&!replies);
  continue;
 }
 assert(!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions&&!ad.MacTabLock);
 assert(allocations==frees);
 if(scenario>=5){
  struct wr_ft_pending_token ticket={0};
  assert(wr_ft_pending_elem_take(&event,&ticket));
  assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&ticket));
  assert(!ad.wr_ft_pending.references[ticket.slot]);
 }
 assert(auth_calls==((scenario==2||scenario==7)?0:1));
 assert(failures==((scenario==1||scenario==6)?1:0));
 assert(replies==((scenario==0||scenario==4||scenario==5)?1:0));
 assert(e->assoc_gen==((scenario==0||scenario==5)?2:1));
 }
 puts("PASS | native FT AUTH branch | real existing/pending scope with modeled entry initialization; reply observes committed generation under live lease; ordinary rejection preserves generation; existing and first-peer resource/allocation exits verified");
 return 0;
}
'''
if a.request_context:
 main=main.replace('if(scenario==3)ad.wr_assoc_generations[7]=~0U;',
                   'exhaust_generation=(scenario==3);')
# Required by pending-scope inline definitions, even though insertion is not executed here.
prefix=prefix.replace('struct {MLME_QUEUE Queue,EAP_Queue;} Mlme;', 'struct wr_iot_peer_close_executor wr_iot_peer_close_executor;struct {MLME_QUEUE Queue,EAP_Queue;} Mlme;')
prefix=prefix.replace('#include "peer-table-owner.h"','#include "peer-table-owner.h"\n#include "peer-close-executor.h"')
with tempfile.TemporaryDirectory(prefix='ft-auth-callback-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(prefix+actors+main)
 subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
