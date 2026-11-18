#!/usr/bin/env python3
"""Exercise composed native enqueue functions and generation guards on the host."""
import argparse
import difflib
import json
import hashlib
from pathlib import Path
import runpy
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('--prepared-driver', type=Path)
p.add_argument('--output', type=Path)
p.add_argument('--patch', type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
compose = runpy.run_path(str(here / 'assoc-generation-composition.py'))['compose']
texts = compose({}, a.source, here)
if a.prepared_driver:
    # Prior composition stages may modify the same SDK files. Compare our exact
    # affected bodies in CI; other predecessor modifications remain intact.
    for name in ('include/assoc-generation.h', 'include/assoc-generation-kernel.h'):
        assert (a.prepared_driver / name).read_text() == texts[name]
    for name in ('common/mlme.c', 'mgmt/mgmt_entrytb.c', 'ap/ap_assoc.c', 'ap/ap_repeater.c'):
        assert '#include "assoc-generation-kernel.h"' in (a.prepared_driver / name).read_text()
    for signature in ('BOOLEAN MlmeEnqueue(', 'BOOLEAN EAPMlmeEnqueue(', 'BOOLEAN MlmeEnqueueForRecv('):
        original = texts['common/mlme.c']
        prepared = (a.prepared_driver/'common/mlme.c').read_text()
        start = original.index(signature)
        body = original[start:original.index('\n}',start)+2]
        assert body in prepared, 'prepared enqueue differs: ' + signature
    assert (a.prepared_driver/'common/cmm_wpa.c').read_text() == texts['common/cmm_wpa.c']
    assert (a.prepared_driver/'ap/ap_assoc.c').read_text().count('if (!wr_assoc_reassociate(pAd, pEntry))') == 2
if a.patch:
    patch = []
    for name, text in sorted(texts.items()):
        old = a.source / name
        patch += difflib.unified_diff(old.read_text().splitlines(True) if old.exists() else [],
            text.splitlines(True), fromfile='a/' + name if old.exists() else '/dev/null', tofile='b/' + name)
    a.patch.write_text(''.join(patch))
s = texts['common/mlme.c']
assert s.count('struct wr_assoc_stamp wr_stamp;') == 3
assert s.count('wr_assoc_publish(') == 4
assert s.count('Queue->Entry[Tail].assoc_gen = Elem->assoc_gen;') == 1
assert s.count('if (!wr_assoc_event_current(pAd, Elem))') == 2
assert texts['common/cmm_wpa.c'].count('wr_assoc_event_entry_current(pAd, Elem, pEntry)') == 4
assert texts['ap/ap_assoc.c'].count('if (!wr_assoc_reassociate(pAd, pEntry))') == 2
assert 'wr_assoc_generations' not in texts['include/rtmp.h'].split('typedef struct _MAC_TABLE {')[1].split('} MAC_TABLE')[0]
# Compose is deliberately single-application and rejects changed native anchors.
try:
    compose(texts, a.source, here)
except ValueError:
    pass
else:
    raise AssertionError('double composition accepted')
functions = []
reset_source = texts['mgmt/mgmt_entrytb.c']
reset_start = reset_source.index('static INT mac_entry_reset(')
reset_body = reset_source[reset_start:reset_source.index('\n}', reset_start)+2]
for signature in ('BOOLEAN MlmeEnqueue(', 'BOOLEAN EAPMlmeEnqueue('):
    start = s.index(signature)
    functions.append(s[start:s.index('\n}', start) + 2])
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define IN
#define TRUE 1
#define FALSE 0
#define MAC_ADDR_LEN 6
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_MLME_QUEUE 4
#define MAX_LEN_OF_EAP_QUEUE 4
#define MGMT_DMA_BUFFER_SIZE 256
#define WPA_STATE_MACHINE 1
#define RESERVED_WCID 255
#define LENGTH_802_11 24
#define RATE_11 11
#define CIPHER_NONE 0
#define RTMPCancelTimer(timer,cancelled) do{(void)(timer);*(cancelled)=1;}while(0)
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 2
#define RTMP_TEST_FLAG(a,b) ((void)(a),(void)(b),0)
#define DBGPRINT_ERR(x) do{}while(0)
#define NdisZeroMemory(p,n) memset(p,0,n)
#define NdisMoveMemory(d,s,n) memcpy(d,s,n)
#define COPY_MAC_ADDR(d,s) memcpy(d,s,6)
#define MAC_ADDR_EQUAL(a,b) (memcmp(a,b,6)==0)
#define IS_ENTRY_NONE(e) (!(e)->valid)
typedef int INT,BOOLEAN;
typedef unsigned int UINT32;
typedef unsigned long ULONG;
typedef void VOID;
struct lock {int held;void *pContent;};
typedef struct lock spinlock_t;
static int spin_trylock_bh(spinlock_t *l){if(l->held)return 0;l->held=1;return 1;}
static int table_held;
static void NdisAcquireSpinLock(struct lock *l){assert(!l->held);l->held=1;}
static void NdisReleaseSpinLock(struct lock *l){assert(l->held);l->held=0;}
typedef struct {unsigned char pad[10],Addr2[6],rest[8];} HEADER_802_11,*PHEADER_802_11;
typedef struct {unsigned assoc_gen;unsigned short assoc_wcid;unsigned char assoc_addr[6];
 unsigned char Msg[256];unsigned long Machine,MsgType,MsgLen,Priv;unsigned Wcid;int Occupied;} MLME_QUEUE_ELEM;
typedef struct {struct lock Lock;int Tail,Num;MLME_QUEUE_ELEM Entry[4];} MLME_QUEUE,EAP_MLME_QUEUE;
typedef struct {unsigned assoc_gen,wcid;unsigned char Addr[6];int valid;
 int RetryTimer,EnqueueStartForPSKTimer,MaxSupportedRate,CurrTxRate;
 struct {int KeyLen,CipherAlg;} PairwiseKey;} MAC_TABLE_ENTRY;
typedef struct {struct lock MacTabLock;unsigned wr_assoc_generations[4];
 struct {MAC_TABLE_ENTRY Content[4];} MacTab;
 struct {MLME_QUEUE Queue,EAP_Queue;} Mlme;} RTMP_ADAPTER;
static MAC_TABLE_ENTRY *MacTableLookup(RTMP_ADAPTER *ad,unsigned char *mac){
 unsigned i;assert(ad->MacTabLock.held);table_held++;
 for(i=1;i<4;i++)if(ad->MacTab.Content[i].valid&&MAC_ADDR_EQUAL(ad->MacTab.Content[i].Addr,mac))return &ad->MacTab.Content[i];
 return NULL;
}
static int MlmeQueueFull(MLME_QUEUE *q,int n){(void)n;return q->Num==4;}
static int EAPMlmeQueueFull(EAP_MLME_QUEUE *q){return q->Num==4;}
#include "assoc-generation-kernel.h"
'''
main = r'''
int main(void){
 RTMP_ADAPTER ad={0};MAC_TABLE_ENTRY *e=&ad.MacTab.Content[1];
 unsigned char mac[6]={1,2,3,4,5,6};MLME_QUEUE_ELEM old,requeued;
 struct wr_assoc_stamp stamp;HEADER_802_11 frame={0};unsigned i;
 ad.MacTabLock.pContent=&ad.MacTabLock;
 e->valid=1;e->wcid=1;COPY_MAC_ADDR(e->Addr,mac);
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);assert(e->assoc_gen==1);
 assert(MlmeEnqueue(&ad,1,2,6,mac,0));old=ad.Mlme.Queue.Entry[0];
 assert(old.assoc_gen==1&&old.assoc_wcid==1&&wr_assoc_event_current(&ad,&old));
 assert(EAPMlmeEnqueue(&ad,1,2,6,mac,0));assert(ad.Mlme.EAP_Queue.Entry[0].assoc_gen==1);
 /* Timer callback refuses immediately when deletion owns the table lock. */
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(!MlmeEnqueue(&ad,1,2,6,mac,0));assert(ad.Mlme.Queue.Num==1);
 assert(!EAPMlmeEnqueue(&ad,1,2,6,mac,0));assert(ad.Mlme.EAP_Queue.Num==1);
 assert(!wr_assoc_event_current(&ad,&old));assert(!wr_assoc_reassociate(&ad,e));
 assert(ad.MacTabLock.held);NdisReleaseSpinLock(&ad.MacTabLock);
 /* Same address in the same slot after deletion/reset/allocation. */
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);
 assert(mac_entry_reset(&ad,e,TRUE)==0);e->valid=1;e->wcid=1;COPY_MAC_ADDR(e->Addr,mac);
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);
 assert(e->assoc_gen==3&&!wr_assoc_event_current(&ad,&old));
 requeued=old;assert(!wr_assoc_event_current(&ad,&requeued));
 assert(MlmeEnqueue(&ad,1,2,6,mac,0));assert(wr_assoc_event_current(&ad,&ad.Mlme.Queue.Entry[1]));
 /* Association in-place, wrong MAC, invalid entry, zero stamp, wrong WCID. */
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);
 assert(!wr_assoc_event_current(&ad,&ad.Mlme.Queue.Entry[1]));
 COPY_MAC_ADDR(frame.Addr2,mac);stamp=wr_assoc_capture(&ad,1,sizeof(frame),&frame,1);
 wr_assoc_publish(&old,&stamp);old.Machine=1;assert(wr_assoc_event_current(&ad,&old));
 e->Addr[0]^=1;assert(!wr_assoc_event_current(&ad,&old));e->Addr[0]^=1;
 e->valid=0;assert(!wr_assoc_event_current(&ad,&old));e->valid=1;
 old.assoc_gen=0;assert(!wr_assoc_event_current(&ad,&old));
 old.assoc_wcid=255;assert(!wr_assoc_event_current(&ad,&old));
 stamp=wr_assoc_capture(&ad,1,5,mac,1);assert(stamp.gen==0);
 stamp=wr_assoc_capture(&ad,1,6,mac,2);assert(stamp.gen==0);
 stamp=wr_assoc_capture(&ad,1,6,NULL,1);assert(stamp.gen==0);
 /* Stamps for unrelated events are initialized, including reused queue cells. */
 assert(MlmeEnqueue(&ad,7,2,6,mac,0));assert(ad.Mlme.Queue.Entry[2].assoc_gen==0);
 assert(wr_assoc_event_current(&ad,&ad.Mlme.Queue.Entry[2]));
 /* Counter survives whole MacTab clear; never wrap and admit old generation. */
 memset(&ad.MacTab,0,sizeof(ad.MacTab));assert(ad.wr_assoc_generations[1]==4);
 ad.wr_assoc_generations[1]=~0U-1U;
 assert(wr_assoc_generation_next(&ad.wr_assoc_generations[1])==~0U);
 for(i=0;i<10;i++)assert(wr_assoc_generation_next(&ad.wr_assoc_generations[1])==0);
 assert(ad.wr_assoc_generations[1]==~0U&&table_held>0);
 /* Execute the same lock-taking helpers composed into allocation/reassociation. */
 e=&ad.MacTab.Content[2];e->wcid=2;e->valid=1;COPY_MAC_ADDR(e->Addr,mac);
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_assoc_advance_locked(&ad,e,2)==1);
 NdisReleaseSpinLock(&ad.MacTabLock);
 stamp=wr_assoc_capture(&ad,1,6,mac,2);wr_assoc_publish(&old,&stamp);old.Machine=1;
 assert(wr_assoc_event_entry_current(&ad,&old,e));
 assert(!wr_assoc_event_entry_current(&ad,&old,&ad.MacTab.Content[1]));
 assert(wr_assoc_reassociate(&ad,e));assert(e->assoc_gen==2);
 wr_assoc_publish(&requeued,&stamp);requeued.Machine=1;
 assert(!wr_assoc_event_current(&ad,&requeued));
 assert(!wr_assoc_event_entry_current(&ad,&old,e));
 stamp=wr_assoc_capture(&ad,1,6,mac,99);assert(stamp.gen==0);
 ad.wr_assoc_generations[2]=~0U;assert(!wr_assoc_reassociate(&ad,e));assert(e->assoc_gen==0);
 assert(!wr_assoc_event_current(&ad,&old));
#ifdef OS_ABL_FUNC_SUPPORT
 ad.MacTabLock.pContent=NULL;assert(!wr_assoc_try_table_lock(&ad));
#endif
 puts("native normal/EAP enqueues and generation guards: PASS");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-assoc-gen-') as directory:
    d = Path(directory)
    (d/'test.c').write_text(prefix+'\n'.join(functions)+reset_body+main)
    for abi in (False, True):
        command = ['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',
            '-Wno-unused-parameter','-fsanitize=address,undefined','-fno-pie','-no-pie',
            '-I'+str(here),str(d/'test.c'),'-o',str(d/'test')]
        if abi:
            command.insert(1,'-DOS_ABL_FUNC_SUPPORT=1')
        subprocess.run(command,check=True)
        subprocess.run([str(d/'test')],check=True)

report = dict(host_native_enqueue_verified=True, composition_anchors_verified=True,
    same_mac_wcid_reuse_rejected=True, counter_wrap_refused=True,
    timer_lock_contention_refusal_verified=True, os_abl_lock_unwrap_host_verified=True,
    execution_lifetime_pin_verified=False, target_compiled=False, runtime_verified=False,
    prepared_driver_checked=a.prepared_driver is not None,
    output_sha256={name:hashlib.sha256(text.encode()).hexdigest() for name,text in texts.items()},
    input_sha256={name:hashlib.sha256((a.source/name).read_bytes()).hexdigest()
        for name in texts if (a.source/name).exists()})
if a.output:
    a.output.write_text(json.dumps(report,indent=2)+'\n')
