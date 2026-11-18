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
# Represent the real predecessor: the full native implementation is private;
# the public transaction wrapper is provided by an include, not this C body.
staged=(a.source/'mgmt/mgmt_entrytb.c').read_text().replace(
    'MAC_TABLE_ENTRY *MacTableInsertEntry(',
    'static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(',1)
staged+='\n#include "wr-iot-peer-normal-insert.inc"\n'
staged_result=compose({'mgmt/mgmt_entrytb.c':staged},a.source,here)
staged_output=staged_result['mgmt/mgmt_entrytb.c']
start=staged_output.index('static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(')
end=staged_output.index('\n}',start)+2
assert staged_output[start:end].count('if(pEntry) wr_assoc_publish_slot_locked(pAd,pEntry);')==1
assert staged_output.count('if(pEntry) wr_assoc_publish_slot_locked(pAd,pEntry);')==1
assert staged_output.endswith('#include "wr-iot-peer-normal-insert.inc"\n')

texts['common/cmm_wpa.c']=runpy.run_path(str(here/'ra2-gtk-request-composition.py'))['compose'](texts['common/cmm_wpa.c'])
texts['ap/ap_wpa.c']=runpy.run_path(str(here/'ra2-rekey-composition.py'))['compose']((a.source/'ap/ap_wpa.c').read_text())
texts['include/ra2-gtk-request-kernel.h']=(here/'ra2-gtk-request-kernel.h').read_text()
texts['include/ra2-rekey-admission.h']=(here/'ra2-rekey-admission.h').read_text()
if a.prepared_driver:
    # Prior composition stages may modify the same SDK files. Compare our exact
    # affected bodies in CI; other predecessor modifications remain intact.
    for name in ('include/assoc-generation.h', 'include/assoc-generation-kernel.h', 'include/ra2-gtk-request-kernel.h'):
        expected_header=texts[name]
        if name=='include/ra2-gtk-request-kernel.h' and (a.prepared_driver/'include/ra2-mutation-admission-kernel.h').exists():
            expected_header=runpy.run_path(str(here/'ra2-key-arbitration-composition.py'))['request_header'](expected_header)
        assert (a.prepared_driver / name).read_text() == expected_header
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
    for name in ('mgmt/mgmt_entrytb.c','ap/ap_repeater.c'):
        assert (a.prepared_driver/name).read_text().count('if(pEntry) wr_assoc_publish_slot_locked(pAd,pEntry);') == 1
    assert 'WRITE_ONCE(pAd->wr_assoc_visible[wcid],0); smp_wmb();' in (a.prepared_driver/'mgmt/mgmt_entrytb.c').read_text()
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
retry_source=(a.source/'ap/ap_wpa.c').read_text()
retry_start=retry_source.index('VOID WPARetryExec(')
retry_body=retry_source[retry_start:retry_source.index('\n}',retry_start)+2]
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
/* Linux current macro must stay defined while compiling the real helpers. */
#define get_current() (current_thread_info()->task)
#define current get_current()
#define IN
#define READ_ONCE(x) __atomic_load_n(&(x),__ATOMIC_RELAXED)
#define WRITE_ONCE(x,v) __atomic_store_n(&(x),(v),__ATOMIC_RELAXED)
static void (*read_hook)(void);
static void read_barrier(void){__atomic_thread_fence(__ATOMIC_ACQUIRE);if(read_hook)read_hook();}
#define smp_rmb() read_barrier()
#define smp_wmb() __atomic_thread_fence(__ATOMIC_RELEASE)
#define TRUE 1
#define FALSE 0
#define MAC_ADDR_LEN 6
#define MAX_LEN_OF_MAC_TABLE 4
#define MAX_LEN_OF_MLME_QUEUE 4
#define MAX_LEN_OF_EAP_QUEUE 4
#define MGMT_DMA_BUFFER_SIZE 256
#define WPA_STATE_MACHINE 1
#define MT2_EAPOLTIMEOUT 2
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
typedef void *PVOID;
struct lock {int held;void *pContent;};
typedef struct lock spinlock_t;
static int spin_trylock_bh(spinlock_t *l){if(l->held)return 0;l->held=1;return 1;}
static int table_held;
static void NdisAcquireSpinLock(struct lock *l){assert(!l->held);l->held=1;}
static void NdisReleaseSpinLock(struct lock *l){assert(l->held);l->held=0;}
typedef struct {unsigned char pad[4],Addr1[6],Addr2[6],rest[8];} HEADER_802_11,*PHEADER_802_11;
typedef struct {unsigned assoc_gen;unsigned short assoc_wcid;unsigned char assoc_addr[6];
 unsigned char Msg[256];unsigned long Machine,MsgType,MsgLen,Priv;unsigned Wcid;int Occupied;} MLME_QUEUE_ELEM;
typedef struct {struct lock Lock;int Tail,Num;MLME_QUEUE_ELEM Entry[4];} MLME_QUEUE,EAP_MLME_QUEUE;
typedef struct {unsigned assoc_gen,wcid;unsigned char Addr[6];int valid;
 void *pAd;int RetryTimer,EnqueueStartForPSKTimer,MaxSupportedRate,CurrTxRate;
 struct {int KeyLen,CipherAlg;} PairwiseKey;} MAC_TABLE_ENTRY;
typedef struct {struct lock MacTabLock;unsigned wr_assoc_generations[4],wr_assoc_visible[4],wr_assoc_event_users[4];unsigned char wr_assoc_addr[4][6];
 struct {MAC_TABLE_ENTRY Content[4];} MacTab;
 struct {MLME_QUEUE Queue,EAP_Queue;} Mlme;} RTMP_ADAPTER;
static __attribute__((unused)) MAC_TABLE_ENTRY *MacTableLookup(RTMP_ADAPTER *ad,unsigned char *mac){
 unsigned i;assert(ad->MacTabLock.held);table_held++;
 for(i=1;i<4;i++)if(ad->MacTab.Content[i].valid&&MAC_ADDR_EQUAL(ad->MacTab.Content[i].Addr,mac))return &ad->MacTab.Content[i];
 return NULL;
}
static int MlmeQueueFull(MLME_QUEUE *q,int n){(void)n;return q->Num==4;}
static int EAPMlmeQueueFull(EAP_MLME_QUEUE *q){return q->Num==4;}
#include "assoc-generation-kernel.h"
'''
main = r'''
static RTMP_ADAPTER *hook_adapter;
static unsigned hook_at,hook_count;
static void association_between_reads(void){
 if(++hook_count==hook_at){
  MAC_TABLE_ENTRY *entry=&hook_adapter->MacTab.Content[3];
  read_hook=NULL;
  NdisAcquireSpinLock(&hook_adapter->MacTabLock);
  assert(wr_assoc_advance_locked(hook_adapter,entry,3));
  wr_assoc_publish_slot_locked(hook_adapter,entry);
  NdisReleaseSpinLock(&hook_adapter->MacTabLock);
 }
}
int main(void){
 RTMP_ADAPTER ad={0};MAC_TABLE_ENTRY *e=&ad.MacTab.Content[1];
 unsigned char mac[6]={1,2,3,4,5,6};MLME_QUEUE_ELEM old,requeued;
 struct wr_assoc_stamp stamp;HEADER_802_11 frame={0};unsigned i;
 ad.MacTabLock.pContent=&ad.MacTabLock;
 e->valid=1;e->wcid=1;e->pAd=&ad;COPY_MAC_ADDR(e->Addr,mac);
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);assert(e->assoc_gen==1);wr_assoc_publish_slot_locked(&ad,e);
 assert(MlmeEnqueue(&ad,1,2,6,mac,0));old=ad.Mlme.Queue.Entry[0];
 assert(old.assoc_gen==1&&old.assoc_wcid==1&&wr_assoc_event_current(&ad,&old));
 assert(EAPMlmeEnqueue(&ad,1,2,6,mac,0));assert(ad.Mlme.EAP_Queue.Entry[0].assoc_gen==1);
 /* Unrelated table ownership must not lose a one-shot retry callback. */
 NdisAcquireSpinLock(&ad.MacTabLock);
 WPARetryExec(NULL,e,NULL,NULL);assert(ad.Mlme.Queue.Num==2);
 assert(EAPMlmeEnqueue(&ad,1,2,6,mac,0));assert(ad.Mlme.EAP_Queue.Num==2);
 assert(wr_assoc_event_current(&ad,&old));assert(!wr_assoc_reassociate(&ad,e));
 assert(ad.MacTabLock.held);NdisReleaseSpinLock(&ad.MacTabLock);
 /* Same address in the same slot after deletion/reset/allocation. */
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);
 assert(mac_entry_reset(&ad,e,TRUE)==0);e->valid=1;e->wcid=1;COPY_MAC_ADDR(e->Addr,mac);
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);
 wr_assoc_publish_slot_locked(&ad,e);
 assert(e->assoc_gen==3&&!wr_assoc_event_current(&ad,&old));
 requeued=old;assert(!wr_assoc_event_current(&ad,&requeued));
 assert(MlmeEnqueue(&ad,1,2,6,mac,0));assert(wr_assoc_event_current(&ad,&ad.Mlme.Queue.Entry[2]));
 /* Association in-place, wrong MAC, invalid entry, zero stamp, wrong WCID. */
 e->assoc_gen=wr_assoc_generation_next(&ad.wr_assoc_generations[1]);
 wr_assoc_publish_slot_locked(&ad,e);
 assert(!wr_assoc_event_current(&ad,&ad.Mlme.Queue.Entry[2]));
 COPY_MAC_ADDR(frame.Addr2,mac);stamp=wr_assoc_capture(&ad,1,sizeof(frame),&frame,1);
 wr_assoc_publish(&old,&stamp);old.Machine=1;assert(wr_assoc_event_current(&ad,&old));
 e->Addr[0]^=1;wr_assoc_publish_slot_locked(&ad,e);assert(!wr_assoc_event_current(&ad,&old));e->Addr[0]^=1;wr_assoc_publish_slot_locked(&ad,e);
 e->valid=0;assert(!wr_assoc_event_current(&ad,&old));e->valid=1;
 old.assoc_gen=0;assert(!wr_assoc_event_current(&ad,&old));
 old.assoc_wcid=255;assert(!wr_assoc_event_current(&ad,&old));
 stamp=wr_assoc_capture(&ad,1,5,mac,1);assert(stamp.gen==0);
 stamp=wr_assoc_capture(&ad,1,6,mac,2);assert(stamp.gen==0);
 stamp=wr_assoc_capture(&ad,1,6,NULL,1);assert(stamp.gen==0);
 /* Stamps for unrelated events are initialized, including reused queue cells. */
 assert(MlmeEnqueue(&ad,7,2,6,mac,0));assert(ad.Mlme.Queue.Entry[3].assoc_gen==0);
 assert(wr_assoc_event_current(&ad,&ad.Mlme.Queue.Entry[3]));
 /* Counter survives whole MacTab clear; never wrap and admit old generation. */
 memset(&ad.MacTab,0,sizeof(ad.MacTab));assert(ad.wr_assoc_generations[1]==4);
 ad.wr_assoc_generations[1]=~0U-1U;
 assert(wr_assoc_generation_next(&ad.wr_assoc_generations[1])==~0U);
 for(i=0;i<10;i++)assert(wr_assoc_generation_next(&ad.wr_assoc_generations[1])==0);
 assert(ad.wr_assoc_generations[1]==~0U&&table_held==0);
 /* Execute the same lock-taking helpers composed into allocation/reassociation. */
 e=&ad.MacTab.Content[2];e->wcid=2;e->valid=1;COPY_MAC_ADDR(e->Addr,mac);
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_assoc_advance_locked(&ad,e,2)==1);wr_assoc_publish_slot_locked(&ad,e);
 NdisReleaseSpinLock(&ad.MacTabLock);
 stamp=wr_assoc_capture(&ad,1,6,mac,2);wr_assoc_publish(&old,&stamp);old.Machine=1;
 assert(wr_assoc_event_entry_current(&ad,&old,e));
 assert(!wr_assoc_event_entry_current(&ad,&old,&ad.MacTab.Content[1]));
 ad.wr_assoc_event_users[2]=1;assert(!wr_assoc_reassociate(&ad,e));assert(e->assoc_gen==1);
 ad.wr_assoc_event_users[2]=0;
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
 /* Replace the association at each of the three reader barriers: no mixed stamp. */
 e=&ad.MacTab.Content[3];e->wcid=3;e->valid=1;COPY_MAC_ADDR(e->Addr,mac);
 ad.wr_assoc_generations[3]=1;e->assoc_gen=1;wr_assoc_publish_slot_locked(&ad,e);
 hook_adapter=&ad;
 for(hook_at=1;hook_at<=3;hook_at++){
  hook_count=0;read_hook=association_between_reads;
  stamp=wr_assoc_read_slot(&ad,3,mac);assert(!stamp.gen&&read_hook==NULL);
  stamp=wr_assoc_read_slot(&ad,3,mac);assert(stamp.gen==e->assoc_gen);
 }
 WRITE_ONCE(ad.wr_assoc_visible[3],0);
 stamp=wr_assoc_read_slot(&ad,3,mac);assert(stamp.gen==0);
 /* Same MAC in two live slots cannot identify a MAC-only internal event. */
 {
  RTMP_ADAPTER duplicate={0};MAC_TABLE_ENTRY *first=&duplicate.MacTab.Content[1];
  MAC_TABLE_ENTRY *second=&duplicate.MacTab.Content[2];
  first->valid=second->valid=1;first->wcid=1;second->wcid=2;
  first->assoc_gen=second->assoc_gen=1;
  COPY_MAC_ADDR(first->Addr,mac);COPY_MAC_ADDR(second->Addr,mac);
  wr_assoc_publish_slot_locked(&duplicate,first);wr_assoc_publish_slot_locked(&duplicate,second);
  stamp=wr_assoc_capture(&duplicate,1,6,mac,RESERVED_WCID);assert(!stamp.gen);
  assert(!MlmeEnqueue(&duplicate,1,2,6,mac,0)&&!duplicate.Mlme.Queue.Num);
  assert(!EAPMlmeEnqueue(&duplicate,1,2,6,mac,0)&&!duplicate.Mlme.EAP_Queue.Num);
  stamp=wr_assoc_capture(&duplicate,1,6,mac,1);assert(stamp.gen==1&&stamp.wcid==1);
  stamp=wr_assoc_capture(&duplicate,1,6,mac,2);assert(stamp.gen==1&&stamp.wcid==2);
  second->valid=0;WRITE_ONCE(duplicate.wr_assoc_visible[2],0);
  stamp=wr_assoc_capture(&duplicate,1,6,mac,RESERVED_WCID);assert(stamp.gen==1&&stamp.wcid==1);
  assert(MlmeEnqueue(&duplicate,1,2,6,mac,0));
 }
 puts("native normal/EAP enqueues and generation guards: PASS");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-assoc-gen-') as directory:
    d = Path(directory)
    # Reproduce the target's exact two macro definitions. A function-shaped
    # current macro alone would miss the parameter collision under GNU C.
    mutant=(here/'assoc-generation.h').read_text().replace('current_gen','current')
    (d/'old-name.c').write_text('#define get_current() (current_thread_info()->task)\n'
        '#define current get_current()\n'+mutant)
    rejected=subprocess.run(['gcc','-std=gnu11','-Werror','-fsyntax-only',str(d/'old-name.c')],capture_output=True,text=True)
    assert rejected.returncode and 'current' in rejected.stderr and 'error:' in rejected.stderr
    (d/'test.c').write_text(prefix+'\n'.join(functions)+retry_body+reset_body+main)
    for abi in (False, True):
        command = ['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',
            '-Wno-unused-parameter','-fsanitize=address,undefined','-fno-pie','-no-pie',
            '-I'+str(here),str(d/'test.c'),'-o',str(d/'test')]
        if abi:
            command.insert(1,'-DOS_ABL_FUNC_SUPPORT=1')
        subprocess.run(command,check=True)
        subprocess.run([str(d/'test')],check=True)

report = dict(host_native_enqueue_verified=True, composition_anchors_verified=True,
    same_mac_wcid_reuse_rejected=True, ambiguous_mac_only_capture_refused=True, explicit_duplicate_mac_wcid_capture_verified=True, counter_wrap_refused=True, kernel_current_macro_collision_regression_verified=True, renamed_native_insertion_stage_verified=True,
    timer_enqueue_under_unrelated_table_contention_verified=True, os_abl_lock_unwrap_host_verified=True,
    execution_lifetime_pin_verified=False, target_compiled=False, runtime_verified=False,
    prepared_driver_checked=a.prepared_driver is not None,
    native_one_shot_retry_enqueue_under_contention_verified=True,
    publication_reader_barrier_interleavings_verified=True, publication_reader_barriers_tested=3,
    output_sha256={name:hashlib.sha256(text.encode()).hexdigest() for name,text in texts.items()},
    input_sha256={name:hashlib.sha256((a.source/name).read_bytes()).hexdigest()
        for name in texts if (a.source/name).exists()})
if a.output:
    a.output.write_text(json.dumps(report,indent=2)+'\n')
