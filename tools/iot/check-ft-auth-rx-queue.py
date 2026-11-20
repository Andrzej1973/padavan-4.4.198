#!/usr/bin/env python3
"""Execute AUTH RX binding and both generated native queue clones together."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
argv=sys.argv[:];sys.argv=[str(here/'check-ft-auth-pending-enqueue.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):data=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
native=data['fixture']['prepared']['common/mlme.c']
module=runpy.run_path(str(here/'ft-auth-enqueue-composition.py'))
def generated(fn,name):
 source,proto=fn(native);start=source.rindex('BOOLEAN '+name+'(')
 return source[start:source.index('\n}',start)+2],proto
active,ap=generated(module['compose'],'wr_ft_auth_mlme_enqueue_for_recv')
pending,pp=generated(module['compose_pending'],'wr_ft_auth_pending_enqueue_for_recv')
source=runpy.run_path(str(here/'ft-auth-rx-composition.py'))['compose'](native,ap,pp)
start=source.index('BOOLEAN MlmeEnqueueForRecv(');wrapper=source[start:source.index('\n}',start)+2]
prefix='#include <stdio.h>\n'+data['prefix']
prefix=prefix.replace('if(replace_before_queue){',
 'if(replace_before_queue && lock!=&hook->MacTabLock){')
prefix=prefix.replace('typedef struct {unsigned char Addr1[6],Addr2[6],rest[12];} HEADER_802_11;',
 'typedef struct {struct {unsigned char Type,SubType;} FC;unsigned char duration[2],Addr1[6],Addr2[6],rest[8];} HEADER_802_11;')
prefix=prefix.replace('int MacTabLock;struct {unsigned BssidNum;',
 'int MacTabLock,OpMode;struct {unsigned BssidNum;')
prefix+='''
#define DOT11R_FT_SUPPORT 1
#define OPMODE_AP 1
#define FC_TYPE_MGMT 0
#define SUBTYPE_AUTH 11
#define IS_ENTRY_NONE(e) (!(e)->client)
typedef MAC_TABLE_ENTRY *PMAC_TABLE_ENTRY;
static int fallback_calls;
#include "ft-auth-peer-scope.h"
'''
# Exact native RX signature, with only the fallback actor body replaced.
start=native.index('BOOLEAN MlmeEnqueueForRecv(');declaration=native[start:native.index('{',start)]
fallback=declaration.replace('BOOLEAN MlmeEnqueueForRecv(', 'static BOOLEAN wr_ft_auth_native_mlme_enqueue_for_recv(')+'{ fallback_calls++;return FALSE; }\n'
main=r'''
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
#define RX(n,p) MlmeEnqueueForRecv(&ad,0,&rssi,0,0,n,p,OPMODE_AP)
#else
#define RX(n,p) MlmeEnqueueForRecv(&ad,0,&rssi,n,p,OPMODE_AP)
#endif
int main(void){
 RTMP_ADAPTER ad={0};FRAME_802_11 frame={0};struct raw_rssi_info rssi={0};
 ad.OpMode=OPMODE_AP;ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.bssid[0]=2;
 wr_ft_pending_ledger_init(&ad.wr_ft_pending);
 frame.Hdr.FC.Type=FC_TYPE_MGMT;frame.Hdr.FC.SubType=SUBTYPE_AUTH;
 frame.Hdr.Addr1[0]=2;frame.Hdr.Addr2[0]=42;frame.Octet[0]=2;frame.Octet[2]=1;
 MAC_TABLE_ENTRY *e=&ad.MacTab.Content[7];
 *e=(MAC_TABLE_ENTRY){.assoc_gen=9,.wcid=7,.func_tb_idx=2,.Sst=SST_ASSOC,.client=1,.Addr={42},.wdev=&ad.ApCfg.MBSSID[2].wdev};
 hook=&ad;replace_before_queue=1;
 assert(RX(30,&frame));
 MLME_QUEUE_ELEM *first=&ad.Mlme.Queue.Entry[0];
 assert(first->assoc_gen==9&&first->assoc_wcid==7&&!first->ft_pending_generation);
 assert(e->assoc_gen==10&&!replace_before_queue);
 struct wr_ft_peer_stamp stale={.generation=first->assoc_gen,.wcid=7,.bss=2};
 memcpy(stale.addr,first->assoc_addr,6);
 assert(!wr_ft_peer_current_locked(&ad,&stale));
 struct wr_ft_peer_scope scope={0};MAC_TABLE_ENTRY *borrowed=NULL;
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(!wr_ft_auth_existing_enter_locked(&ad,first,2,frame.Hdr.Addr2,&scope,&borrowed));
 assert(!borrowed&&!scope.active&&!ad.wr_assoc_event_users[7]);
 NdisReleaseSpinLock(&ad.MacTabLock);
 assert(RX(30,&frame));
 MLME_QUEUE_ELEM *fresh=&ad.Mlme.Queue.Entry[1];
 assert(fresh->assoc_gen==10);
 NdisAcquireSpinLock(&ad.MacTabLock);
 fresh->Machine=ACTION_STATE_MACHINE;
 assert(!wr_ft_auth_existing_enter_locked(&ad,fresh,2,frame.Hdr.Addr2,&scope,&borrowed));
 fresh->Machine=AP_AUTH_STATE_MACHINE;
 fresh->Msg[26]=3;
 assert(!wr_ft_auth_existing_enter_locked(&ad,fresh,2,frame.Hdr.Addr2,&scope,&borrowed));
 fresh->Msg[26]=1;
 assert(wr_ft_auth_existing_enter_locked(&ad,fresh,2,frame.Hdr.Addr2,&scope,&borrowed));
 assert(borrowed==e&&scope.active&&ad.wr_assoc_event_users[7]==1);
 assert(wr_ft_peer_leave_locked(&ad,&scope));
 assert(!ad.wr_assoc_event_users[7]&&!ad.wr_iot_peer_table_owner.transactions);
 NdisReleaseSpinLock(&ad.MacTabLock);
 assert(first->Machine==AP_AUTH_STATE_MACHINE&&first->MsgType==APMT2_PEER_AUTH_REQ);
 e->client=0;
 assert(RX(30,&frame));
 MLME_QUEUE_ELEM *second=&ad.Mlme.Queue.Entry[2];
 assert(!second->assoc_gen&&second->ft_pending_generation&&second->ft_pending_bss==2);
 assert(second->ft_pending_addr[0]==42&&second->Wcid==RESERVED_WCID);
 assert(ad.wr_ft_pending.references[second->ft_pending_slot]==1);
 struct wr_ft_pending_token ticket={0},observed={0};
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(!wr_ft_auth_pending_current_locked(&ad,second,0,frame.Hdr.Addr2,&observed));
 assert(!observed.generation);
 assert(wr_ft_auth_pending_current_locked(&ad,second,2,frame.Hdr.Addr2,&observed));
 assert(observed.generation==second->ft_pending_generation);
 assert(ad.wr_ft_pending.references[observed.slot]==1);
 wr_ft_pending_token_clear(&observed);
 assert(wr_ft_pending_retire_key_locked(&ad.wr_ft_pending,2,frame.Hdr.Addr2)==1);
 assert(!wr_ft_auth_pending_current_locked(&ad,second,2,frame.Hdr.Addr2,&observed));
 assert(!observed.generation&&ad.wr_ft_pending.references[second->ft_pending_slot]==1);
 NdisReleaseSpinLock(&ad.MacTabLock);
 assert(wr_ft_pending_elem_take(second,&ticket));
 assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&ticket));
 assert(!ad.wr_ft_pending.references[ticket.slot]);
 assert(ad.Mlme.Queue.Num==3&&!ad.MacTabLock&&!ad.Mlme.Queue.Lock&&!fallback_calls);
 puts("PASS | FT AUTH RX-to-queue | original generation retained across queue-lock reuse; stale callback refused, live callback lease balanced; pending ticket moved once");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-auth-rx-queue-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(prefix+fallback+active+pending+wrapper+main)
 for flags in ([],['-DEAPOL_QUEUE_SUPPORT'],['-DCUSTOMER_DCC_FEATURE']):
  subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
