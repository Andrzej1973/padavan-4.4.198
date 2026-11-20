#!/usr/bin/env python3
"""Check pinned insertion composition and execute its admission/exit fragments.

Native allocation/initialization, hardware and crypto are explicit host actors.
This does not compile the complete vendor insertion function or install it.
"""
import argparse
from pathlib import Path
import runpy
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
base = runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({}, a.source, here)
compose = runpy.run_path(str(here/'ft-pending-insert-composition.py'))['compose']
try:
    compose(base, a.source, here)
except ValueError as error:
    assert 'requires peer-owner predecessor' in str(error)
else:
    raise AssertionError('missing owner predecessor accepted')
# Pinned native source plus owner schema stand-in. Runtime owner behavior uses
# the real headers below; this does not certify the entire staged predecessor.
base['include/rtmp.h'] = base['include/rtmp.h'].replace('\tMAC_TABLE MacTab;',
    ' struct wr_iot_peer_table_owner wr_iot_peer_table_owner;\n'
    ' struct wr_iot_peer_close_executor wr_iot_peer_close_executor;\n\tMAC_TABLE MacTab;', 1)
changed = compose(base, a.source, here)
try:
    compose(changed, a.source, here)
except ValueError:
    pass
else:
    raise AssertionError('duplicate preparation accepted')
# Target candidates can add a second guarded failure (for example, a BSS index
# check) after FT has claimed its ticket. Every locked return must funnel
# through the same cleanup label, including repeated release/return anchors.
multi = dict(base)
locked_failure = ('\t\t\t\t\t\tNdisReleaseSpinLock(&pAd->MacTabLock);\n'
                 '\t\t\t\t\t\treturn NULL;\n')
insert_at = '\tfor (i = FirstWcid;'
native_source = multi['mgmt/mgmt_entrytb.c']
if native_source.count(insert_at) != 1 or native_source.count(locked_failure) != 1:
    raise AssertionError('pinned insertion failure anchors changed')
multi['mgmt/mgmt_entrytb.c'] = native_source.replace(
    insert_at, locked_failure + insert_at, 1)
multi_changed = compose(multi, a.source, here)
multi_source = multi_changed['mgmt/mgmt_entrytb.c']
multi_start = multi_source.index('static MAC_TABLE_ENTRY *wr_ft_pending_native_insert(')
multi_end = multi_source.index('\n}', multi_start)+2
multi_clone = multi_source[multi_start:multi_end]
multi_failure_start = multi_clone.index('\tfor (i = FirstWcid;')
multi_failure_end = multi_clone.index('/* add this MAC entry into HASH table */')
multi_failure_region = multi_clone[multi_failure_start:multi_failure_end]
assert multi_failure_region.count('goto wr_ft_pending_failure;') >= 2
assert 'return NULL;' not in multi_failure_region
s = changed['mgmt/mgmt_entrytb.c']
start = s.index('static MAC_TABLE_ENTRY *wr_ft_pending_native_insert(')
end = s.index('\n}', start)+2
clone = s[start:end]
gate = clone[clone.index(' if(!wr_ticket'):clone.index('\tfor (i = FirstWcid;')]
finish = clone[clone.index('if(pEntry && !wr_ft_pending_peer_publish_locked'):clone.rindex('NdisReleaseSpinLock(&pAd->MacTabLock);', 0, clone.index('wr_ft_pending_failure:\n'))]
failure = clone[clone.index('wr_ft_pending_failure:\n'):clone.rindex('\n}')]
start = s.index('MAC_TABLE_ENTRY *wr_ft_pending_insert(')
wrapper = s[start:s.index('\n}', start)+2]
assert clone.index('NdisAcquireSpinLock(&pAd->MacTabLock);') < clone.index(gate)
assert clone.index(gate) < clone.index('mac_entry_reset(pAd, pEntry, CleanAll);')
assert clone.index('/* add this MAC entry into HASH table */') < clone.index(finish)
assert clone.index('wr_assoc_publish_slot_locked(pAd,pEntry)') < clone.index(finish)
reserve_call='if(!wr_ft_pending_peer_reserve_slot_locked(pAd,i,wdev,wr_ticket,wr_scope)) {'
assert clone.index(reserve_call) < clone.index('mac_entry_reset(pAd, pEntry, CleanAll);')
assert clone.index('wr_ft_pending_peer_publish_locked(pAd,pEntry,wr_ticket,wr_scope)') > clone.index('wr_assoc_publish_slot_locked(pAd,pEntry)')
assert 'wr_ft_pending_peer_cancel_slot_locked(pAd,wr_scope)' in failure
assert clone.index(finish) < clone.index('rtmp_tx_burst_set(pAd);')
assert clone[clone.index('\tfor (i = FirstWcid;'):clone.index(finish)].count('return NULL;') == 0
assert 'wr_ft_pending_ledger_init' not in changed['include/rtmp.h'].split('struct _RTMP_ADAPTER {', 1)[1]
assert changed['common/rtmp_init.c'].count('wr_ft_pending_ledger_init(&pAd->wr_ft_pending);') == 1
# Check every byte outside the new ordinary-insert retirement hook is preserved.
signature = 'MAC_TABLE_ENTRY *MacTableInsertEntry('
start = base['mgmt/mgmt_entrytb.c'].index(signature)
end = base['mgmt/mgmt_entrytb.c'].index('\n}', start)+2
original = base['mgmt/mgmt_entrytb.c'][start:end]
ordinary = s[s.index(signature):s.index('\n}', s.index(signature))+2]
retire = '''
#ifdef DOT11R_FT_SUPPORT
 if(pEntry)wr_ft_pending_retire_key_locked(&pAd->wr_ft_pending,pEntry->func_tb_idx,pEntry->Addr);
#endif
 '''
completion_init = '''
#ifdef R1KH_HARD_RETRY
			RTMP_OS_INIT_COMPLETION(&pEntry->ack_r1kh);
#endif /* R1KH_HARD_RETRY */'''
assert ordinary.count('RTMP_OS_INIT_COMPLETION(&pEntry->ack_r1kh);') == 1
assert ordinary.index('mac_entry_reset(pAd, pEntry, CleanAll);') < ordinary.index(completion_init)
assert ordinary.replace(retire, '', 1).replace(completion_init, '', 1) == original
# Check the existing private/startup owner-gate form too; never remove its gate.
private = original.replace(signature, 'static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(', 1)
private = private.replace('IN BOOLEAN CleanAll)', 'IN BOOLEAN CleanAll,\n const struct wr_iot_peer_open_ticket *wr_open_ticket,unsigned long wr_open_lease)', 1)
private = private.replace('NdisAcquireSpinLock(&pAd->MacTabLock);', 'NdisAcquireSpinLock(&pAd->MacTabLock);\n#include "wr-iot-peer-startup-insertion-gate.inc"', 1)
private_input = dict(base)
private_input['mgmt/mgmt_entrytb.c'] = base['mgmt/mgmt_entrytb.c'].replace(original, private, 1)
private_out = compose(private_input, a.source, here)['mgmt/mgmt_entrytb.c']
assert 'TRUE,NULL,0,ticket,scope);' in private_out
private_start = private_out.index('static MAC_TABLE_ENTRY *wr_ft_pending_native_insert(')
private_body = private_out[private_start:private_out.index('\n}', private_start)+2]
assert private_body.index('#include "wr-iot-peer-startup-insertion-gate.inc"') < private_body.index(' if(!wr_ticket')

prefix = r'''
#include <assert.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
#define MAC_ADDR_LEN 6
#define MAX_LEN_OF_MAC_TABLE 4
#define WR_FT_PENDING_CAPACITY MAX_LEN_OF_MAC_TABLE
#define HW_BEACON_MAX_NUM 3
#define RESERVED_WCID 0
#define ENTRY_CLIENT 1
#define OPMODE_AP 1
#define TRUE 1
#define IS_ENTRY_NONE(e) (!(e)->used)
#define IS_ENTRY_CLIENT(e) ((e)->client)
#define MAC_ADDR_EQUAL(a,b) (!memcmp(a,b,6))
#define NdisZeroMemory(a,n) memset(a,0,n)
#include "ft-pending-identity.h"
#include "peer-table-owner.h"
#include "peer-close-executor.h"
typedef unsigned char UCHAR;
struct wifi_dev {unsigned func_idx;};
typedef struct {unsigned used,client,wcid,assoc_gen,func_tb_idx,Sst;unsigned char Addr[6];struct wifi_dev *wdev;} MAC_TABLE_ENTRY;
typedef struct {int MacTabLock;struct wr_ft_pending_ledger wr_ft_pending;
 unsigned wr_assoc_generations[MAX_LEN_OF_MAC_TABLE],wr_assoc_visible[MAX_LEN_OF_MAC_TABLE],wr_assoc_event_users[MAX_LEN_OF_MAC_TABLE];unsigned char wr_assoc_addr[MAX_LEN_OF_MAC_TABLE][MAC_ADDR_LEN];
 struct {unsigned BssidNum;struct {struct wifi_dev wdev;} MBSSID[3];} ApCfg;
 struct {MAC_TABLE_ENTRY Content[4];} MacTab;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_peer_close_executor wr_iot_peer_close_executor;} RTMP_ADAPTER;
static inline void wr_assoc_publish_slot_locked(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){
 unsigned int i,wcid=entry->wcid;ad->wr_assoc_visible[wcid]=0;
 for(i=0;i<MAC_ADDR_LEN;i++)ad->wr_assoc_addr[wcid][i]=entry->Addr[i];
 ad->wr_assoc_visible[wcid]=entry->assoc_gen;
}
#include "ft-pending-peer-scope.h"
static int fail_insert,fail_publish,tail_calls;
static void NdisAcquireSpinLock(int *lock){assert(!*lock);*lock=1;}
static void NdisReleaseSpinLock(int *lock){assert(*lock);*lock=0;}
static MAC_TABLE_ENTRY *wr_ft_pending_native_insert(RTMP_ADAPTER *pAd,UCHAR *pAddr,
 struct wifi_dev *wdev,int ent_type,int OpMode,int CleanAll,
 const struct wr_ft_pending_token *wr_ticket,struct wr_ft_pending_peer_scope *wr_scope){
 unsigned int wr_slot;int i;int wr_claimed=0;MAC_TABLE_ENTRY *pEntry=NULL;
 (void)CleanAll;
 NdisAcquireSpinLock(&pAd->MacTabLock);
'''
actor = r'''
 /* Explicit host allocation actor; gate and exits above/below are extracted. */
 if(fail_insert)goto wr_ft_pending_failure;
 for(wr_slot=1;wr_slot<MAX_LEN_OF_MAC_TABLE;wr_slot++){
  if(!pAd->MacTab.Content[wr_slot].used){
   pEntry=&pAd->MacTab.Content[wr_slot];
   i=wr_slot;
'''+clone[clone.index(reserve_call):clone.index('\t\t\tmac_entry_reset(pAd, pEntry, CleanAll);')]+r'''
   pEntry->used=1;pEntry->client=1;pEntry->wcid=wr_slot;
   pEntry->assoc_gen=++pAd->wr_assoc_generations[wr_slot];
   pAd->wr_assoc_visible[wr_slot]=pEntry->assoc_gen;
   pEntry->func_tb_idx=wdev->func_idx;pEntry->wdev=wdev;
   memcpy(pEntry->Addr,pAddr,6);
   assert(wr_ft_pending_claimed_locked(&pAd->wr_ft_pending,wr_ticket));
   assert(pEntry->wcid==wr_scope->wcid&&pEntry->client&&pEntry->assoc_gen);
   assert(pEntry->assoc_gen==pAd->wr_assoc_generations[wr_slot]&&pEntry->assoc_gen==pAd->wr_assoc_visible[wr_slot]);
   assert(pEntry->func_tb_idx==wr_scope->bss&&pEntry->wdev==&pAd->ApCfg.MBSSID[wr_scope->bss].wdev);
   assert(!memcmp(pEntry->Addr,wr_ticket->addr,MAC_ADDR_LEN));
   assert(wr_scope->adapter==pAd&&wr_scope->generation==0&&wr_scope->active);
   assert(!memcmp(wr_scope->addr,wr_ticket->addr,MAC_ADDR_LEN));
   if(fail_publish)pEntry->wdev=&pAd->ApCfg.MBSSID[0].wdev;
   break;
'''
actor += r'''
  }
 }
'''
tail = r'''
 NdisReleaseSpinLock(&pAd->MacTabLock);
 assert(pAd->wr_iot_peer_table_owner.transactions);tail_calls++;
 return pEntry;
'''
main = r'''
static void ordinary_insert_retire(RTMP_ADAPTER *pAd,MAC_TABLE_ENTRY *pEntry){
 NdisAcquireSpinLock(&pAd->MacTabLock);
'''+retire+r'''
 NdisReleaseSpinLock(&pAd->MacTabLock);
}
static void leave_scope(RTMP_ADAPTER *pAd,struct wr_ft_pending_peer_scope *scope){
 NdisAcquireSpinLock(&pAd->MacTabLock);
 assert(wr_ft_pending_peer_leave_locked(pAd,scope));
 NdisReleaseSpinLock(&pAd->MacTabLock);
}
int main(void){
 RTMP_ADAPTER ad={0};UCHAR mac[6]={42};struct wr_ft_pending_token first,sibling;
 MAC_TABLE_ENTRY *entry;unsigned long reset;unsigned i;
 struct wr_ft_pending_peer_scope scope={0};
 ad.ApCfg.BssidNum=3;for(i=0;i<3;i++)ad.ApCfg.MBSSID[i].wdev.func_idx=i;
 /* Same MAC on BSS0 must not be adopted by a BSS2 first-peer event. */
 ad.MacTab.Content[1]=(MAC_TABLE_ENTRY){.used=1,.client=1,.wcid=1,.assoc_gen=1,.func_tb_idx=0,.Addr={42},.wdev=&ad.ApCfg.MBSSID[0].wdev};
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,mac,&first));
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,mac,&sibling));
 assert(!wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[1].wdev,&first,&scope));
 assert(wr_ft_pending_current_locked(&ad.wr_ft_pending,&first)&&!ad.MacTabLock);
 fail_insert=1;
 assert(!wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[2].wdev,&first,&scope));
 assert(wr_ft_pending_current_locked(&ad.wr_ft_pending,&first)&&!ad.MacTabLock);
 fail_insert=0;
 entry=wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[2].wdev,&first,&scope);
 assert(entry==&ad.MacTab.Content[2]&&entry->func_tb_idx==2&&tail_calls==1&&scope.generation==entry->assoc_gen);
 /* A second invocation cannot erase an outstanding insertion lease. */
 {
 struct wr_ft_pending_peer_scope saved=scope;
 unsigned users=ad.wr_assoc_event_users[2],owners=ad.wr_iot_peer_table_owner.transactions;
 assert(!wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[2].wdev,&first,&scope));
 assert(!memcmp(&saved,&scope,sizeof(scope)));
 assert(ad.wr_assoc_event_users[2]==users&&ad.wr_iot_peer_table_owner.transactions==owners);
 }
 leave_scope(&ad,&scope);
 assert(!wr_ft_pending_current_locked(&ad.wr_ft_pending,&sibling));
 assert(!wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[2].wdev,&sibling,&scope));
 assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&first));
 assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&sibling));
 /* Even an inactive target-context entry prevents a duplicate first-peer insert. */
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,mac,&first));
 assert(!wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[2].wdev,&first,&scope));
 ordinary_insert_retire(&ad,entry);
 assert(!wr_ft_pending_current_locked(&ad.wr_ft_pending,&first));
 assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&first));
 memset(&ad.MacTab.Content[2],0,sizeof(*entry));
 assert(wr_ft_pending_reserve_locked(&ad.wr_ft_pending,2,mac,&first));
 reset=wr_iot_peer_table_begin(&ad.wr_iot_peer_table_owner);assert(reset);
 assert(!wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[2].wdev,&first,&scope));
 assert(wr_iot_peer_table_finish(&ad.wr_iot_peer_table_owner,reset,1));
 assert(!ad.MacTabLock&&!ad.wr_iot_peer_table_owner.transactions);
 /* Full allocation failure returns the authority for a later retry. */
 ad.MacTab.Content[2].used=ad.MacTab.Content[3].used=1;
 assert(!wr_ft_pending_insert(&ad,mac,&ad.ApCfg.MBSSID[2].wdev,&first,&scope));
 assert(wr_ft_pending_current_locked(&ad.wr_ft_pending,&first));
 assert(wr_ft_pending_release_locked(&ad.wr_ft_pending,&first));
 assert(!ad.MacTabLock&&!ad.wr_iot_peer_table_owner.transactions);
 /* Publication failure retains the slot lease, retires the ticket and
  * stops before native post-unlock side effects or AUTH delivery. */
 {
 RTMP_ADAPTER broken={0};struct wr_ft_pending_peer_scope held={0};
 struct wr_ft_pending_token ticket={0};int before=tail_calls;
 broken.ApCfg.BssidNum=3;broken.ApCfg.MBSSID[2].wdev.func_idx=2;
 assert(wr_ft_pending_reserve_locked(&broken.wr_ft_pending,2,mac,&ticket));
 fail_publish=1;
 assert(!wr_ft_pending_insert(&broken,mac,&broken.ApCfg.MBSSID[2].wdev,&ticket,&held));
 fail_publish=0;
 assert(tail_calls==before&&!broken.MacTabLock);
 assert(broken.wr_iot_peer_table_owner.poisoned&&held.active&&!held.generation);
 assert(broken.wr_assoc_event_users[1]==1&&broken.wr_iot_peer_table_owner.transactions==1);
 assert(!wr_ft_pending_current_locked(&broken.wr_ft_pending,&ticket));
 assert(wr_ft_pending_release_locked(&broken.wr_ft_pending,&ticket));
 assert(!wr_ft_pending_peer_leave_locked(&broken,&held));
 }
 puts("PASS | FT pending insertion gates | exact BSS+MAC, foreign-BSS duplicate, stale sibling, retry, capacity, owner and lock balance");
 puts("PASS | FT pending insertion failure | active scope preserved; publication failure retains ownership and prevents AUTH delivery and native tail");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-pending-insert-') as td:
    root = Path(td)
    fixture = root/'check.c'
    fixture.write_text(prefix+gate+actor+finish+tail+failure+'\n}\n'+wrapper+main)
    subprocess.run(['gcc', '-std=gnu99', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-DDOT11R_FT_SUPPORT', '-I'+str(here), str(fixture),
                    '-o', str(root/'check')], check=True)
    subprocess.run([str(root/'check')], check=True)
print('PASS | FT pending insertion composition | pinned anchors, native bookkeeping preserved, private startup gates retained, duplicate preparation refused')
