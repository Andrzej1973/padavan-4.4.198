#!/usr/bin/env python3
"""Execute the complete pending-ticket enqueue clone with host queue actors."""
import argparse
import ast
from pathlib import Path
import runpy
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args();here=Path(__file__).resolve().parent
prepared=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)
api=runpy.run_path(str(here/'ft-pending-enqueue-composition.py'))
prepared['include/mlme.h']=api['queue_fields'](prepared['include/mlme.h'])
prepared['include/mlme.h']=api['queue_closed_field'](prepared['include/mlme.h'])
changed,prototype=api['compose'](prepared['common/mlme.c'])
fields=prepared['include/mlme.h']
assert 'ft_pending_generation' in fields
assert 'wr_ft_pending_closed' in fields
for fn,arg in [(api['compose'],changed),(api['queue_fields'],fields),(api['queue_closed_field'],fields)]:
    try:fn(arg)
    except ValueError:pass
    else:raise AssertionError('duplicate accepted')
start=changed.rindex('BOOLEAN wr_ft_pending_enqueue_for_recv(')
body=changed[start:changed.index('\n}',start)+2]
assert 'wr_assoc_capture(' not in body and 'MacTabLock' not in body
added='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-pending-queue.h"\n'+prototype+'\n'+body+'\n#endif\n'
assert changed.replace(added,'',1)==prepared['common/mlme.c']
life=api['lifecycle'](changed)
handler=life[life.index('VOID MlmeHandler('):life.index('\n}',life.index('VOID MlmeHandler('))+2]
assert handler.index('wr_ft_pending_elem_current_locked(pAd,Elem)') < handler.index('switch (Elem->Machine)')
assert handler.index('switch (Elem->Machine)') < handler.index('wr_ft_pending_elem_release(pAd,Elem)') < handler.rindex('Elem->Occupied = FALSE;')
restart=life[life.index('VOID MlmeRestartStateMachine('):life.index('\n}',life.index('VOID MlmeRestartStateMachine('))+2]
assert restart.index('pAd->Mlme.bRunning = TRUE;') < restart.index('wr_ft_pending_closed=1') < restart.index('wr_ft_pending_queue_discard_all')
assert restart.index('wr_ft_pending_queue_discard_all') < restart.index('wr_ft_pending_closed=0') < restart.index('pAd->Mlme.bRunning = FALSE;')
halt=life[life.index('VOID MlmeHalt('):life.index('\n}',life.index('VOID MlmeHalt('))+2]
assert halt.index('RtmpOSTaskKill(pTask)') < halt.index('wr_ft_pending_closed=1') < halt.index('wr_ft_pending_queue_discard_all') < halt.index('MlmeQueueDestroy(')
assert 'wr_ft_pending_elem_init(&Queue->Entry[i]);' in life
assert 'wr_ft_pending_closed=0;' in life
# Reuse the existing native queue/classifier actors, with new metadata fields.
tree=ast.parse((here/'check-ft-enqueue-generation.py').read_text())
prefix=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets))
prefix=prefix.replace('typedef struct {unsigned assoc_gen;',
 'typedef struct {unsigned ft_pending_generation,ft_pending_slot,ft_pending_bss;unsigned char ft_pending_addr[6];unsigned assoc_gen;',1)
prefix=prefix.replace('typedef struct {int Lock,Tail,Num;MLME_QUEUE_ELEM Entry[4];}',
 'typedef struct {int Lock,Tail,Num,wr_ft_pending_closed;MLME_QUEUE_ELEM Entry[4];}',1)
prefix=prefix.replace('typedef struct {struct {unsigned BssidNum;',
 '#include "ft-pending-identity.h"\ntypedef struct {struct wr_ft_pending_ledger wr_ft_pending;int MacTabLock;struct {unsigned BssidNum;',1)
prefix+='\n#define NdisZeroMemory(p,n) memset(p,0,n)\n#define FT_ACTION_BT_REQ 1\n#include "ft-pending-queue.h"\n'
main=r'''
#if defined(CUSTOMER_DCC_FEATURE) || defined(NEIGHBORING_AP_STAT)
#define SEND(n,f) wr_ft_pending_enqueue_for_recv(&ad,0,&rssi,0,0,n,f,0,&ticket)
#else
#define SEND(n,f) wr_ft_pending_enqueue_for_recv(&ad,0,&rssi,n,f,0,&ticket)
#endif
int main(void){
 RTMP_ADAPTER ad={0};struct wr_ft_pending_ledger ledger;struct wr_ft_pending_token ticket={0},taken={0},snapshot={0};
 FRAME_802_11 frame={0};struct raw_rssi_info rssi={0};FT_ACTION *action=(FT_ACTION *)frame.Octet;
 MLME_QUEUE_ELEM *elem=&ad.Mlme.Queue.Entry[0];unsigned generation;
 unsigned char mac[6]={42};ad.ApCfg.BssidNum=3;ad.ApCfg.MBSSID[2].wdev.bssid[0]=2;
 frame.Hdr.Addr1[0]=2;frame.Hdr.Addr2[0]=42;
 action->Category=6;action->Action=1;action->StaMac[0]=42;action->TargetApAddr[0]=2;
 wr_ft_pending_ledger_init(&ledger);
 assert(wr_ft_pending_reserve_locked(&ledger,2,mac,&ticket));generation=ticket.generation;
 assert(!SEND(sizeof(frame)-1,&frame)&&ticket.generation==generation);
 action->Action=3;assert(!SEND(sizeof(frame),&frame)&&ticket.generation==generation);action->Action=1;
 frame.Hdr.Addr1[0]=1;assert(!SEND(sizeof(frame),&frame));frame.Hdr.Addr1[0]=2;
 elem->Occupied=1;assert(!SEND(sizeof(frame),&frame)&&ticket.generation==generation);elem->Occupied=0;
 ad.Mlme.Queue.Num=4;assert(!SEND(sizeof(frame),&frame)&&ticket.generation==generation);ad.Mlme.Queue.Num=0;
 ad.Mlme.Queue.wr_ft_pending_closed=1;assert(!SEND(sizeof(frame),&frame)&&ticket.generation==generation);ad.Mlme.Queue.wr_ft_pending_closed=0;
 elem->ft_pending_generation=99;assert(!SEND(sizeof(frame),&frame));elem->ft_pending_generation=0;
 assert(SEND(sizeof(frame),&frame)&&!ticket.generation);
 assert(elem->ft_pending_generation==generation&&elem->Occupied&&elem->Wcid==0);
 assert(elem->Machine==ACTION_STATE_MACHINE&&!elem->assoc_gen&&ad.Mlme.Queue.Num==1);
 assert(ledger.references[elem->ft_pending_slot]==1); /* move, never duplicate ref */
 assert(wr_ft_pending_elem_snapshot(elem,&snapshot));
 assert(snapshot.generation==generation&&snapshot.bss==2&&!memcmp(snapshot.addr,mac,6));
 assert(elem->ft_pending_generation==generation&&ledger.references[snapshot.slot]==1);
 taken.generation=1;assert(!wr_ft_pending_elem_snapshot(elem,&taken)); /* occupied token owner */
 wr_ft_pending_token_clear(&taken);
 wr_ft_pending_token_clear(&snapshot);
 assert(!SEND(sizeof(frame),&frame));
 assert(wr_ft_pending_elem_take(elem,&taken)&&!elem->ft_pending_generation);
 assert(!wr_ft_pending_elem_take(elem,&taken));
 assert(wr_ft_pending_current_locked(&ledger,&taken));
 assert(wr_ft_pending_release_locked(&ledger,&taken));wr_ft_pending_token_clear(&taken);
 assert(!wr_ft_pending_elem_take(elem,&taken));
 /* Retired ticket still moves as its original identity; consumer must drop it. */
 elem->Occupied=0;ad.Mlme.Queue.Tail=0;ad.Mlme.Queue.Num=0;
 assert(wr_ft_pending_reserve_locked(&ledger,2,mac,&ticket));
 assert(wr_ft_pending_retire_key_locked(&ledger,2,mac)==1);
 assert(SEND(sizeof(frame),&frame)&&!ticket.generation);
 assert(wr_ft_pending_elem_take(elem,&taken)&&!wr_ft_pending_current_locked(&ledger,&taken));
 assert(wr_ft_pending_release_locked(&ledger,&taken));
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-pending-enqueue-') as td:
    root=Path(td);source=root/'check.c';exe=root/'check'
    source.write_text(prefix+prototype+'\n'+body+main)
    for flags in ([],['-DEAPOL_QUEUE_SUPPORT'],['-DCUSTOMER_DCC_FEATURE']):
        subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(source),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('PASS | FT pending native enqueue | one-reference move, failed-enqueue retention, terminating BT_REQ context, full/occupied/closed/live-ticket refusal, immutable stale identity, EAP/SNR variants')
print('PASS | FT pending queue lifecycle composition | metadata init, stale drop, post-dispatch release, restart close/drain/reopen and halt drain before destroy')
print('PASS | FT pending queue transport | one-shot take, explicit release owner, native enqueue unchanged; lifecycle remains uninstalled')
