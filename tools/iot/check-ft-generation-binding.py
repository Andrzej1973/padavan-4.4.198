#!/usr/bin/env python3
"""Execute composed active-peer RRB stamps and pending first-peer FT leases."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('--success-context',action='store_true');a=p.parse_args()
here=Path(__file__).resolve().parent
# Reuse the established full native callback fixtures and all their assertions.
argv=sys.argv[:];sys.argv=[str(here/'check-ft-parser-composition.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):data=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
mlme=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)['common/mlme.c']
module=runpy.run_path(str(here/'ft-enqueue-generation-composition.py'))
_,prototype=module['compose'](mlme)
pending_enqueue=runpy.run_path(str(here/'ft-pending-enqueue-composition.py'))
_,pending_prototype=pending_enqueue['compose'](mlme)
rx_prepared=runpy.run_path(str(here/'ft-rx-generation-composition.py'))['compose'](
 mlme,prototype,pending_prototype)
rx_wrapper=rx_prepared[rx_prepared.index('BOOLEAN MlmeEnqueueForRecv('):]
rx_wrapper=rx_wrapper[:rx_wrapper.index('\n}')+2]
assert 'wr_frame->Hdr.Addr1' in rx_wrapper and 'wr_entry->func_tb_idx==wr_apidx' in rx_wrapper
assert 'wr_entry->wdev==&pAd->ApCfg.MBSSID[wr_apidx].wdev' in rx_wrapper
assert 'wr_action->Action==FT_ACTION_BT_REQ' in rx_wrapper
assert 'wr_ft_mlme_enqueue_for_recv' in rx_wrapper and 'wr_ft_pending_enqueue_for_recv' in rx_wrapper
assert rx_wrapper.index('NdisAcquireSpinLock(&pAd->MacTabLock)') < rx_wrapper.index('wr_ft_pending_reserve_locked')
assert 'wr_ft_pending_release_locked' in rx_wrapper
insert_prototype='''#ifdef DOT11R_FT_SUPPORT
struct wr_ft_pending_peer_scope;
MAC_TABLE_ENTRY *wr_ft_pending_insert(RTMP_ADAPTER *,UCHAR *,struct wifi_dev *,
 const struct wr_ft_pending_token *,struct wr_ft_pending_peer_scope *);
#endif'''
prepared=module['bind_ft'](data['text'],prototype,pending_prototype,insert_prototype)
if a.success_context:
 prepared,_=runpy.run_path(str(here/'ft-auth-request-context-composition.py'))['compose_ft'](
  prepared,(a.source/'include/ft.h').read_text())
def function(name):
 start=prepared.index('VOID '+name+'(');return prepared[start:prepared.index('\n}',start)+2]
assert prepared.count('wr_ft_peer_capture_locked(')==1
assert prepared.count('wr_ft_peer_enter_locked(')==1 and prepared.count('wr_ft_peer_leave_locked(')==1
rrb_prepared=function('FT_RrbHandler')
assert rrb_prepared.index('wr_ft_pending_reserve_locked') < rrb_prepared.index('MlmeAllocateMemory')
assert 'wr_ft_pending_enqueue_for_recv' in rrb_prepared and 'wr_ft_mlme_enqueue_for_recv' in rrb_prepared
request_prepared=prepared[prepared.index('case FT_ACTION_BT_REQ:'):prepared.index('case FT_ACTION_BT_CONFIRM:')]
assert 'wr_ft_pending_insert(' in request_prepared and 'MacTableInsertEntry(' not in request_prepared
try:module['bind_ft'](prepared,prototype)
except ValueError:pass
else:raise AssertionError('duplicate binding accepted')

def types(text):
 text="#define MAC_ADDR_LEN 6\n"+text
 text=text.replace('#include <string.h>','#include <string.h>\n#include "peer-table-owner.h"\n'
  '#define MAX_LEN_OF_MAC_TABLE 8\n#define WR_FT_PENDING_CAPACITY 8\n'
  '#define RESERVED_WCID 0\n#define SST_AUTH 1\n#define SST_ASSOC 2\n'
  '#define WRITE_ONCE(location,value) ((location)=(value))\n#define smp_wmb() ((void)0)\n'
  '#include "ft-pending-identity.h"\n#include "peer-close-executor.h"\n'
  '#define IS_ENTRY_NONE(e) (!(e)->client)\n#define FT_ACTION_BT_REQ 1\n#define Action action')
 text=text.replace('struct wifi_dev {int id;};','struct wifi_dev {unsigned char bssid[6];unsigned func_idx;};')
 text=text.replace('struct wifi_dev{unsigned char bssid[6];};','struct wifi_dev{unsigned char bssid[6];unsigned func_idx;};')
 text=text.replace('unsigned wcid;int client','unsigned assoc_gen,wcid;int client')
 text=text.replace('unsigned int wcid;int func_tb_idx','unsigned int assoc_gen,wcid;int func_tb_idx')
 text=text.replace('typedef struct {int MacTabLock;struct',
  'typedef struct {int MacTabLock;unsigned wr_iot_peer_delete_active,wr_assoc_event_users[8],wr_assoc_generations[8],wr_assoc_visible[8];unsigned char wr_assoc_addr[8][6];struct wr_ft_pending_ledger wr_ft_pending;struct wr_iot_peer_close_executor wr_iot_peer_close_executor;struct wr_iot_peer_table_owner wr_iot_peer_table_owner;struct')
 text=text.replace('} AD,*PRTMP_ADAPTER;','} AD,*PRTMP_ADAPTER;\ntypedef AD RTMP_ADAPTER;typedef ENTRY MAC_TABLE_ENTRY;')
 return text
prefix=types(data['action_prefix'])
if a.success_context:
 prefix='#include <stdio.h>\n'+prefix
 prefix=prefix.replace('#define SST_AUTH 1',
  '#define SST_NOT_AUTH 0\n#define SST_AUTH 1\n#include "ft-iapp-request-state.h"')
 prefix=prefix.replace('typedef struct {int MacTabLock;',
  'typedef struct {struct wr_ft_iapp_request_state wr_ft_iapp_requests;int MacTabLock;')
 prefix=prefix.replace('typedef ENTRY MAC_TABLE_ENTRY;',
  'typedef ENTRY MAC_TABLE_ENTRY;\n#include "ft-auth-request-context.h"')
 prefix=prefix.replace('FT_AuthReqHandler(AD *ad,ENTRY *e,FT_INFO *in,FT_INFO *out){',
  'FT_AuthReqHandler(AD *ad,ENTRY *e,FT_INFO *in,FT_INFO *out,const struct wr_ft_auth_request_context *context){(void)context;')
prefix=prefix.replace('typedef struct {ULONG MsgLen;unsigned Wcid;unsigned char Msg[256];}',
 'typedef struct {ULONG MsgLen;unsigned Wcid,assoc_gen,assoc_wcid,ft_pending_generation,ft_pending_slot,ft_pending_bss;unsigned char assoc_addr[6],ft_pending_addr[6],Msg[256];}')
prefix=prefix.replace('fail_insert;','fail_insert,expect_scope=1;')
for actor in ('reqs','confirms'):
 prefix=prefix.replace(actor+'++;return MLME_SUCCESS;',
  'assert(!expect_scope||(ad->wr_assoc_event_users[e->wcid]==1&&ad->wr_iot_peer_table_owner.transactions==1));'+actor+'++;return MLME_SUCCESS;')
prefix=prefix.replace('.wcid=7,.client=1','.assoc_gen=1,.wcid=7,.client=1')
main=data['action_main'].replace('.MsgLen=38,.Wcid=7','.MsgLen=38,.Wcid=7,.assoc_gen=1,.assoc_wcid=7,.assoc_addr={42}')
main=main.replace('AD ad={0};ad.ApCfg.BssidNum=3;',
 'AD ad={0};ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.func_idx=2;wr_ft_pending_ledger_init(&ad.wr_ft_pending);')
main=main.replace('MLME_QUEUE_ELEM event={.MsgLen=38,.Wcid=7,.assoc_gen=1,.assoc_wcid=7,.assoc_addr={42}};',
 'MLME_QUEUE_ELEM event={.MsgLen=38,.Wcid=7,.assoc_gen=1,.assoc_wcid=7,.assoc_addr={42}},duplicate={.MsgLen=38,.Wcid=RESERVED_WCID};')
main=main.replace('.wcid=7,.client=1','.assoc_gen=1,.wcid=7,.client=1')
main=main.replace('*wrong=(ENTRY){.wcid=3,.client=1,.func_tb_idx=0,.Sst=SST_ASSOC,.Addr={42},.wdev=&ad.ApCfg.MBSSID[0].wdev};',
 '*wrong=(ENTRY){.wcid=3,.client=1,.func_tb_idx=0,.Sst=SST_ASSOC,.Addr={42},.wdev=&ad.ApCfg.MBSSID[0].wdev};\n ad.wr_assoc_generations[7]=1;ad.wr_assoc_visible[7]=1;memcpy(ad.wr_assoc_addr[7],right->Addr,6);')
main=main.replace('act->Action=FT_ACTION_BT_CONFIRM;FT_FtAction(&ad,&event);assert(confirms==1);',
 '''act->Action=FT_ACTION_BT_CONFIRM;FT_FtAction(&ad,&event);
 assert(!confirms&&!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
 event.assoc_gen=2;FT_FtAction(&ad,&event);assert(confirms==1);''')
main=main.replace('right->client=0;fail_insert=1;', '''event.assoc_gen=0;expect_scope=0;right->client=0;
 struct wr_ft_pending_token ticket={0},sibling={0};NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,right->Addr,&ticket));
 NdisReleaseSpinLock(&ad.MacTabLock);assert(wr_ft_pending_elem_publish(&event,&ticket));
 fail_insert=1;FT_FtAction(&ad,&event);assert(reqs==1&&inserted==1);
 assert(wr_ft_pending_elem_release(&ad,&event));
 fail_insert=0;ticket=(struct wr_ft_pending_token){0};NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,right->Addr,&ticket));
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,right->Addr,&sibling));
 NdisReleaseSpinLock(&ad.MacTabLock);duplicate=event;duplicate.Wcid=RESERVED_WCID;
 assert(wr_ft_pending_elem_publish(&event,&ticket));assert(wr_ft_pending_elem_publish(&duplicate,&sibling));
 FT_FtAction(&ad,&event);assert(inserted==2);assert(reqs==2);
 assert(ad.wr_assoc_event_users[1]==0&&!ad.wr_iot_peer_table_owner.transactions);
 assert(ad.MacTab.Content[1].Sst==SST_AUTH&&ad.MacTab.Content[1].assoc_gen==2);
 assert(wr_ft_pending_elem_release(&ad,&event));
 FT_FtAction(&ad,&duplicate);assert(reqs==2&&inserted==2);
 assert(wr_ft_pending_elem_release(&ad,&duplicate));
 ticket=(struct wr_ft_pending_token){0};NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,right->Addr,&ticket));
 NdisReleaseSpinLock(&ad.MacTabLock);assert(wr_ft_pending_elem_publish(&event,&ticket));
 right->client=1;right->Sst=SST_ASSOC;FT_FtAction(&ad,&event);
 assert(reqs==2&&inserted==2);assert(wr_ft_pending_elem_release(&ad,&event));right->client=0;''')
main=main.replace('right->client=0;FT_FtAction(&ad,&event);assert(reqs==1&&inserted==1);\n fail_insert=0;FT_FtAction(&ad,&event);assert(reqs==2&&inserted==2&&right->Sst==SST_AUTH);',
 'right->client=0;')
main=main.replace('assert(allocs==frees&&!ad.MacTabLock);',
 'assert(allocs==frees&&!ad.MacTabLock&&!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);')

probe_anchor='ad.wr_assoc_generations[7]=1;ad.wr_assoc_visible[7]=1;memcpy(ad.wr_assoc_addr[7],right->Addr,6);'
assert main.count(probe_anchor)==1
main=main.replace(probe_anchor,probe_anchor+r"""
 {
 struct wr_ft_iapp_token_ledger ledger;
 struct wr_ft_iapp_token_handle pending={0},reply={0};
 struct wr_ft_peer_stamp stamp={0};struct wr_ft_peer_scope scope={0};
 unsigned char token[7]={1,2,3,4,5,6,7};
 wr_ft_iapp_token_ledger_init(&ledger);
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_ft_peer_capture_locked(&ad,7,2,right->Addr,&stamp));
 assert(wr_ft_iapp_token_reserve_locked(&ledger,token,2,7,1,right->Addr,
  ad.ApCfg.MBSSID[2].wdev.bssid,&pending));
 assert(!wr_ft_iapp_peer_admit_locked(&ad,&ledger,token,right->Addr,
  ad.ApCfg.MBSSID[2].wdev.bssid,&stamp,&pending,&reply));
 assert(wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 {
 unsigned saved_serial=pending.serial;
 assert(!wr_ft_iapp_peer_admit_locked(&ad,&ledger,token,right->Addr,
  ad.ApCfg.MBSSID[2].wdev.bssid,&stamp,&pending,&pending));
 assert(pending.serial==saved_serial);
 assert(ledger.entry[pending.slot].state==WR_FT_IAPP_TOKEN_WAITING);
 }

 {
 struct wr_ft_iapp_token_handle stale=pending;
 stale.serial++;
 assert(!wr_ft_iapp_peer_admit_locked(&ad,&ledger,token,right->Addr,
  ad.ApCfg.MBSSID[2].wdev.bssid,&stamp,&stale,&reply));
 assert(!reply.serial&&ledger.entry[pending.slot].state==WR_FT_IAPP_TOKEN_WAITING);
 }

 for(unsigned fault=0;fault<6;fault++){
  if(fault==0)right->assoc_gen=2;
  if(fault==1)right->func_tb_idx=0;
  if(fault==2)ad.wr_iot_peer_table_owner.poisoned=1;
  if(fault==3)ad.wr_assoc_visible[7]=0;
  if(fault==4)right->wdev=&ad.ApCfg.MBSSID[0].wdev;
  if(fault==5)ad.wr_assoc_addr[7][0]^=1;
  assert(!wr_ft_iapp_peer_admit_locked(&ad,&ledger,token,right->Addr,
   ad.ApCfg.MBSSID[2].wdev.bssid,&stamp,&pending,&reply));
  assert(!reply.serial&&ledger.entry[pending.slot].state==WR_FT_IAPP_TOKEN_WAITING);
  assert(ad.wr_assoc_event_users[7]==1&&ad.wr_iot_peer_table_owner.transactions==1);
  right->assoc_gen=1;right->func_tb_idx=2;
  right->wdev=&ad.ApCfg.MBSSID[2].wdev;
  memcpy(ad.wr_assoc_addr[7],right->Addr,6);
  ad.wr_iot_peer_table_owner.poisoned=0;ad.wr_assoc_visible[7]=1;
 }
 assert(wr_ft_iapp_peer_admit_locked(&ad,&ledger,token,right->Addr,
  ad.ApCfg.MBSSID[2].wdev.bssid,&stamp,&pending,&reply));
 assert(ad.wr_assoc_event_users[7]==1&&ad.wr_iot_peer_table_owner.transactions==1);
 {
 struct wr_ft_iapp_token_handle duplicate={0};
 assert(!wr_ft_iapp_peer_admit_locked(&ad,&ledger,token,right->Addr,
  ad.ApCfg.MBSSID[2].wdev.bssid,&stamp,&pending,&duplicate));
 assert(!duplicate.serial);
 }
 {
 struct wr_ft_iapp_token_handle unrelated={0};
 unsigned char other_token[7]={8,9,10,11,12,13,14};
 unsigned char other_mac[6]={43};
 assert(wr_ft_iapp_token_reserve_locked(&ledger,other_token,0,3,9,
  other_mac,ad.ApCfg.MBSSID[0].wdev.bssid,&unrelated));
 assert(!wr_ft_iapp_peer_leave_locked(&ad,&scope,&ledger,&unrelated));
 assert(scope.active&&ledger.entry[unrelated.slot].state==WR_FT_IAPP_TOKEN_WAITING);
 assert(wr_ft_iapp_token_request_end_locked(&ledger,&unrelated));
 }
 assert(!wr_ft_iapp_peer_advance_locked(&ad,right,&scope,&ledger,&pending));
 assert(right->assoc_gen==1&&scope.stamp.generation==1);
 assert(!wr_ft_iapp_peer_leave_locked(&ad,&scope,&ledger,&pending));
 assert(scope.active&&pending.serial);
 assert(ad.wr_assoc_event_users[7]==1&&ad.wr_iot_peer_table_owner.transactions==1);
 assert(wr_ft_iapp_token_finish_locked(&ledger,&reply));
 assert(wr_ft_iapp_token_request_end_locked(&ledger,&pending));
 token[0]=99;
 assert(wr_ft_iapp_peer_request_begin_locked(&ad,&ledger,token,&stamp,&pending));
 {
 unsigned saved_serial=pending.serial;
 assert(!wr_ft_iapp_peer_request_begin_locked(&ad,&ledger,token,&stamp,&pending));
 assert(pending.serial==saved_serial);
 }
 assert(wr_ft_iapp_peer_leave_locked(&ad,&scope,&ledger,&pending));
 assert(!scope.active&&!pending.serial&&!ad.wr_assoc_event_users[7]);
 /* Fresh protocol scenario, then restore the pre-existing callback fixture seed. */
 assert(wr_ft_peer_capture_locked(&ad,7,2,right->Addr,&stamp));
 assert(wr_ft_peer_enter_locked(&ad,&stamp,&scope));
 token[0]=100;
 assert(wr_ft_iapp_peer_request_begin_locked(&ad,&ledger,token,&stamp,&pending));
 assert(wr_ft_iapp_peer_advance_locked(&ad,right,&scope,&ledger,&pending));
 assert(!pending.serial&&right->assoc_gen==2&&scope.stamp.generation==2);
 assert(!wr_ft_iapp_token_claim_locked(&ledger,token,right->Addr,
  ad.ApCfg.MBSSID[2].wdev.bssid,&reply));
 assert(wr_ft_iapp_peer_leave_locked(&ad,&scope,&ledger,&pending));
 right->assoc_gen=1;ad.wr_assoc_generations[7]=1;ad.wr_assoc_visible[7]=1;

 NdisReleaseSpinLock(&ad.MacTabLock);
 }
""")

if a.success_context:
 extra=r'''
 for(unsigned mode=0;mode<3;mode++){
  AD trial={0};trial.ApCfg.BssidNum=3;
  trial.ApCfg.MBSSID[2].wdev.bssid[0]=2;
  trial.ApCfg.MBSSID[2].FtCfg.FtCapFlag.Dot11rFtEnable=1;
  ENTRY *peer=&trial.MacTab.Content[7];
  *peer=(ENTRY){.assoc_gen=5,.wcid=7,.client=1,.func_tb_idx=2,.Sst=SST_ASSOC,
   .Addr={42},.wdev=&trial.ApCfg.MBSSID[2].wdev};
  trial.wr_assoc_generations[7]=trial.wr_assoc_visible[7]=5;
  memcpy(trial.wr_assoc_addr[7],peer->Addr,6);
  MLME_QUEUE_ELEM queued={.MsgLen=38,.Wcid=7,.assoc_gen=5,.assoc_wcid=7,.assoc_addr={42}};
  HEADER_802_11 *header=(void *)queued.Msg;header->Addr1[0]=2;header->Addr2[0]=42;
  FT_ACTION *request=(void *)(queued.Msg+24);request->Action=FT_ACTION_BT_REQ;
  request->StaMac[0]=42;request->TargetApAddr[0]=2;
  struct wr_ft_iapp_request_state *state=&trial.wr_ft_iapp_requests;
  struct wr_ft_iapp_token_handle handle={0},claim={0};unsigned char token[7]={1};
  wr_ft_iapp_request_state_init(state);
  assert(wr_ft_iapp_token_reserve_locked(&state->ledger,token,2,7,5,
   peer->Addr,peer->wdev->bssid,&handle));
  state->current[7]=handle;state->detached[7]=(mode!=2);state->detached_sst[7]=SST_ASSOC;
  if(mode==1)assert(wr_ft_iapp_token_claim_locked(&state->ledger,token,
   peer->Addr,peer->wdev->bssid,&claim));
  int old_reqs=reqs,old_forwards=forwards;expect_scope=1;
  FT_FtAction(&trial,&queued);
  assert(reqs==old_reqs+1&&allocs==frees&&!trial.MacTabLock);
  if(mode==0){
   assert(peer->Sst==SST_AUTH&&peer->assoc_gen==6);
   assert(!state->current[7].serial&&!state->detached[7]);
   assert(!trial.wr_assoc_event_users[7]&&!trial.wr_iot_peer_table_owner.transactions);
  }else{
   assert(peer->Sst==SST_ASSOC&&peer->assoc_gen==5&&forwards==old_forwards);
   assert(trial.wr_iot_peer_table_owner.poisoned&&trial.wr_iot_peer_table_owner.transactions==1);
   assert(trial.wr_assoc_event_users[7]==1&&state->current[7].serial==handle.serial);
   assert(state->ledger.entry[handle.slot].state==(mode==1?WR_FT_IAPP_TOKEN_CLAIMED:WR_FT_IAPP_TOKEN_WAITING));
  }
 }
 puts("PASS | native FT Action success retirement | detached WAITING cancelled before state/generation; CLAIMED and synchronous request block reply/transition, retain poisoned lease; buffers balanced");
'''
 at=main.rindex('return 0;')
 main=main[:at]+extra+main[at:]
consumer=prefix+'\n#include "ft-peer-generation.h"\n#include "assoc-generation.h"\n'
consumer+='\n#include "ft-iapp-peer-admission.h"\n'
consumer+='''\n#include "ft-pending-peer-scope.h"\n#include "ft-pending-queue.h"\n'''
consumer+='''\nstatic inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){
 unsigned int i,w=entry->wcid;ad->wr_assoc_visible[w]=0;
 for(i=0;i<MAC_ADDR_LEN;i++)ad->wr_assoc_addr[w][i]=entry->Addr[i];
 ad->wr_assoc_visible[w]=entry->assoc_gen;
}
static MAC_TABLE_ENTRY *wr_ft_pending_insert(RTMP_ADAPTER *ad,UCHAR *mac,
 struct wifi_dev *wdev,const struct wr_ft_pending_token *ticket,
 struct wr_ft_pending_peer_scope *scope){
 MAC_TABLE_ENTRY *entry=0;unsigned int wcid;
 inserted++;if(!ad||!mac||!wdev||!ticket||!scope||fail_insert)return 0;
 NdisAcquireSpinLock(&ad->MacTabLock);
 if(!wr_ft_pending_current_locked(&ad->wr_ft_pending,ticket)||
    !wr_ft_pending_claim_locked(&ad->wr_ft_pending,ticket)){
  NdisReleaseSpinLock(&ad->MacTabLock);return 0;
 }
 for(wcid=1;wcid<MAX_LEN_OF_MAC_TABLE;wcid++)
  if(IS_ENTRY_NONE(&ad->MacTab.Content[wcid]))break;
 if(wcid<MAX_LEN_OF_MAC_TABLE&&wr_ft_pending_peer_reserve_slot_locked(ad,wcid,wdev,ticket,scope)){
  entry=&ad->MacTab.Content[wcid];memset(entry,0,sizeof(*entry));
  entry->wcid=wcid;entry->client=1;entry->func_tb_idx=ticket->bss;entry->wdev=wdev;
  memcpy(entry->Addr,mac,MAC_ADDR_LEN);
  entry->assoc_gen=wr_assoc_generation_next(&ad->wr_assoc_generations[wcid]);
  wr_assoc_publish_slot_locked(ad,entry);
  if(!wr_ft_pending_peer_publish_locked(ad,entry,ticket,scope))entry=0;
  else (void)wr_ft_pending_retire_key_locked(&ad->wr_ft_pending,ticket->bss,mac);
 }else (void)wr_ft_pending_unclaim_locked(&ad->wr_ft_pending,ticket);
 NdisReleaseSpinLock(&ad->MacTabLock);return entry;
}
'''+function('FT_FtAction')+main

prefix=types(data['base'])
prefix+='''
typedef unsigned char UCHAR;
#define NdisZeroMemory(a,n) memset(a,0,n)
#include "ft-peer-generation.h"
struct raw_rssi_info {unsigned char raw_rssi[3],raw_snr;};
static unsigned observed_gen;static int replace_on_alloc;
'''
actors=data['actors'].replace('allocated++;return 0;',
 'allocated++;if(replace_on_alloc){ad->MacTab.Content[7].assoc_gen++;replace_on_alloc=0;}return 0;')
enqueue=r'''
static int wr_ft_mlme_enqueue_for_recv(AD *ad,ULONG wcid,struct raw_rssi_info *rssi,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 UCHAR snr0,UCHAR snr1,
#endif
 ULONG len,void *msg,UCHAR mode,const struct wr_ft_peer_stamp *expected){
 (void)ad;(void)rssi;(void)msg;(void)mode;
 observed_gen=expected->generation;enqueued++;queued_wcid=wcid;queued_length=len;return 1;
}
'''
main=data['main'].replace('.wcid=7,.func_tb_idx=2','.assoc_gen=1,.wcid=7,.func_tb_idx=2')
main=main.replace('assert(ad.MacTabLock==0);return 0;',r'''
 right->assoc_gen=5;replace_on_alloc=1;observed_gen=0;
 packet=calloc(1,38);assert(packet);packet[0]=2;r=(FT_RRB*)(packet+14);r->FTActLen=14;
 ((FT_ACTION*)r->Oct)->StaMac[0]=42;FT_RrbHandler(&ad,packet,38);free(packet);
 assert(observed_gen==5&&right->assoc_gen==6&&!replace_on_alloc);
 assert(ad.MacTabLock==0);return 0;
''')
prefix=types(data['base'])+'''
typedef unsigned char UCHAR;
#define NdisZeroMemory(a,n) memset(a,0,n)
#include "ft-peer-generation.h"
struct raw_rssi_info {unsigned char raw_rssi[3],raw_snr;};
static unsigned observed_gen;static int replace_on_alloc;
'''
enqueue_actor=r'''
static int pending_enqueues,fail_pending_enqueue;static struct wr_ft_pending_token queued_ticket;
static int wr_ft_pending_enqueue_for_recv(AD *ad,ULONG wcid,struct raw_rssi_info *rssi,
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
 UCHAR snr0,UCHAR snr1,
#endif
 ULONG len,void *msg,UCHAR mode,struct wr_ft_pending_token *ticket){
 (void)rssi;(void)len;(void)msg;(void)mode;assert(ad&&!wcid&&ticket&&ticket->generation);
 if(fail_pending_enqueue)return 0;
 queued_ticket=*ticket;wr_ft_pending_token_clear(ticket);pending_enqueues++;return 1;
}
'''
rrb_main=data['main']
rrb_main=rrb_main.replace('.wcid=7,.func_tb_idx=2','.assoc_gen=1,.wcid=7,.func_tb_idx=2')
rrb_main=rrb_main.replace('AD ad={0};ad.ApCfg.BssidNum=3;',
 'AD ad={0};ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.bssid[0]=2;wr_ft_pending_ledger_init(&ad.wr_ft_pending);')
rrb_main=rrb_main.replace('((FT_ACTION*)r->Oct)->StaMac[0]=42;',
 '((FT_ACTION*)r->Oct)->StaMac[0]=42;((FT_ACTION*)r->Oct)->Action=FT_ACTION_BT_REQ;((FT_ACTION*)r->Oct)->TargetApAddr[0]=2;')
rrb_main=rrb_main.replace('FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&queued_wcid==7&&queued_length==38);',
 'struct wr_ft_peer_stamp probe={0};assert(wr_ft_peer_capture_locked(&ad,7,2,right->Addr,&probe));FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&queued_wcid==7&&queued_length==38);')
rrb_main=rrb_main.replace('right->client=0;\n FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1);right->client=1;',
 '''right->client=0;
 FT_RrbHandler(&ad,packet,38);
 assert(pending_enqueues==1&&queued_ticket.generation&&queued_ticket.bss==2&&queued_ticket.addr[0]==42);
 assert(ad.wr_ft_pending.references[queued_ticket.slot]==1);
 NdisAcquireSpinLock(&ad.MacTabLock);assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&queued_ticket));NdisReleaseSpinLock(&ad.MacTabLock);
 assert(!ad.wr_ft_pending.references[queued_ticket.slot]);
 fail_pending_enqueue=1;FT_RrbHandler(&ad,packet,38);
 assert(pending_enqueues==1);for(int i=0;i<WR_FT_PENDING_CAPACITY;i++)assert(!ad.wr_ft_pending.references[i]);
 fail_pending_enqueue=0;allocated=freed=1;
 right->client=1;''')
rrb_main=rrb_main.replace('right->Sst=0;FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1);right->Sst=SST_ASSOC;',
 'right->Sst=0;FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1&&pending_enqueues==0);right->Sst=SST_ASSOC;')
rrb_main=rrb_main.replace('fail_alloc=1;FT_RrbHandler(&ad,packet,38);assert(enqueued==1&&allocated==1&&freed==1);fail_alloc=0;',
 '''right->client=0;fail_alloc=1;FT_RrbHandler(&ad,packet,38);
 assert(enqueued==1&&allocated==1&&freed==1);
 for(int i=0;i<WR_FT_PENDING_CAPACITY;i++)assert(!ad.wr_ft_pending.references[i]);
 fail_alloc=0;right->client=1;''')
producer=prefix+actors+enqueue_actor+enqueue+function('FT_RrbHandler')+rrb_main
with tempfile.TemporaryDirectory(prefix='wr-ft-generation-bind-') as td:
 for name,code in [('producer',producer),('consumer',consumer)]:
  src=Path(td)/(name+'.c');exe=Path(td)/name;src.write_text(code)
  for flags in ([],['-DCUSTOMER_DCC_FEATURE']):
   subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(src),'-o',str(exe)],check=True)
   subprocess.run([str(exe)],check=True)
print('PASS | prepared FT BSS/generation binding | active RRB peer stamp; absent peer requires local-BSS BT_REQ ticket; first-peer insertion advances generation under lease')
print('PASS | pending FT race/failure cases | enqueue/allocation failure releases ticket; failed insert retries; sibling ticket and active-peer race refuse; callback lease balances')
print('PASS | FT callback bounds | stale generation refused; ordinary RX ingress is separately host-checked; paired enqueue-to-callback target compile remains open; prepared code stays uninstalled')
