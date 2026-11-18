#!/usr/bin/env python3
"""Witness native AP GTK software mutations after association reuse, before write guard."""
import argparse
import ast
import hashlib
import json
import hashlib
from pathlib import Path
import runpy
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
p.add_argument('--prepared-driver',type=Path)
p.add_argument('--output',type=Path)
a=p.parse_args()
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']
texts=compose({},a.source,here)
source=(a.prepared_driver/'common/cmm_wpa.c').read_text() if a.prepared_driver else texts['common/cmm_wpa.c']
anchor='if (peerKeyInfo.KeyType == GROUPKEY)'
# Select the AP REQUEST branch, not supplicant/group response handling.
start=source.index('else if ((peerKeyInfo.Request == 1) && (peerKeyInfo.Error == 0))')
start=source.index(anchor,start)
brace=source.index('{',start)
depth=1;end=brace+1
while depth:
    if source[end]=='{':depth+=1
    elif source[end]=='}':depth-=1
    end+=1
body=source[brace+1:end-1]
assert body.count('WPAInstallSharedKey(')==1
assert body.count('wr_assoc_event_entry_current(pAd, Elem, pEntry)')==1
assert body.index('GenRandom(')<body.index('WpaDeriveGTK(')<body.index('WPAStart2WayGroupHS(')<body.index('wr_assoc_event_entry_current(')
# Reuse only the reviewed SDK boundary types/macros, never execute its runner.
tree=ast.parse((here/'check-assoc-generation.py').read_text())
prefix=[ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign)
    and any(isinstance(target,ast.Name) and target.id=='prefix' for target in node.targets)]
assert len(prefix)==1
prefix=prefix[0]
prefix=prefix.replace('unsigned assoc_gen,wcid;', 'unsigned assoc_gen,wcid;int WpaState,GTKState,ReTryCounter;unsigned char func_tb_idx;')
insert='''
typedef unsigned char UINT8;
#define RT_DEBUG_TRACE 0
#define DBGPRINT(level,args) do{}while(0)
#define LEN_TKIP_GTK 32
#define AS_PTKINITDONE 5
#define REKEY_NEGOTIATING 6
#define GROUP_MSG1_RETRY_TIMER_CTR 7
#define IS_ENTRY_CLIENT(entry) ((entry)->valid)
#define GET_GroupKey_WCID(ad,wcid,idx) do{(void)(ad);(wcid)=100+(idx);}while(0)
struct wifi_dev {unsigned char bssid[6];unsigned GroupKeyWepStatus,DefaultKeyId;};
typedef struct {struct wifi_dev wdev;unsigned char GMK[32],GNonce[32],GTK[32];} BSS_STRUCT;
'''
prefix=prefix.replace('typedef struct {struct lock MacTabLock;',insert+'\ntypedef struct {struct lock MacTabLock;struct {BSS_STRUCT MBSSID[3];} ApCfg;')
actors=r'''
static int inject_reuse,derive_calls,handshake_calls,install_calls;
static RTMP_ADAPTER *active;
static void GenRandom(RTMP_ADAPTER *ad,unsigned char *bssid,unsigned char *nonce){
 (void)bssid;memset(nonce,0x51,32);
 if(inject_reuse){
  MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[1];
  NdisAcquireSpinLock(&ad->MacTabLock);
  assert(wr_assoc_advance_locked(ad,entry,1));
  wr_assoc_publish_slot_locked(ad,entry);
  NdisReleaseSpinLock(&ad->MacTabLock);
 }
}
static void WpaDeriveGTK(unsigned char *gmk,unsigned char *nonce,unsigned char *bssid,unsigned char *gtk,unsigned len){
 (void)gmk;(void)nonce;(void)bssid;assert(len==32);memset(gtk,0x72,len);derive_calls++;
}
static void WPAStart2WayGroupHS(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){
 assert(ad==active&&entry==&ad->MacTab.Content[1]);
 assert(entry->assoc_gen==(unsigned)(inject_reuse?2:1));handshake_calls++;
}
static void WPAInstallSharedKey(RTMP_ADAPTER *ad,unsigned cipher,unsigned idx,unsigned key,unsigned wcid,int tx,unsigned char *gtk,unsigned len){
 (void)cipher;(void)tx;(void)gtk;assert(ad==active&&idx==2&&key==2&&wcid==102&&len==32);install_calls++;
}
'''
wrapper='static void native_group_request(RTMP_ADAPTER *pAd,MLME_QUEUE_ELEM *Elem,MAC_TABLE_ENTRY *pEntry){\n int i;unsigned char apidx=pEntry->func_tb_idx;\n'+body+'\n}\n'
main=r'''
int main(void){
 int reuse;
 for(reuse=0;reuse<=1;reuse++){
  RTMP_ADAPTER ad={0};MAC_TABLE_ENTRY *entry=&ad.MacTab.Content[1];MLME_QUEUE_ELEM event={0};
  unsigned char mac[6]={1,2,3,4,5,6};struct wr_assoc_stamp stamp;
  active=&ad;ad.MacTabLock.pContent=&ad.MacTabLock;
  entry->valid=1;entry->wcid=1;entry->func_tb_idx=2;entry->WpaState=AS_PTKINITDONE;
  COPY_MAC_ADDR(entry->Addr,mac);ad.wr_assoc_generations[1]=1;entry->assoc_gen=1;
  wr_assoc_publish_slot_locked(&ad,entry);stamp=wr_assoc_capture(&ad,1,6,mac,1);
  wr_assoc_publish(&event,&stamp);event.Machine=1;
  ad.ApCfg.MBSSID[2].wdev.DefaultKeyId=1;
  assert(wr_assoc_event_entry_current(&ad,&event,entry));
  inject_reuse=reuse;derive_calls=handshake_calls=install_calls=0;
  native_group_request(&ad,&event,entry);
  assert(derive_calls==1&&handshake_calls==1);
  assert(ad.ApCfg.MBSSID[2].wdev.DefaultKeyId==2);
  assert(ad.ApCfg.MBSSID[2].GNonce[0]==0x51&&ad.ApCfg.MBSSID[2].GTK[0]==0x72);
  assert(entry->GTKState==REKEY_NEGOTIATING&&entry->ReTryCounter==GROUP_MSG1_RETRY_TIMER_CTR);
  assert(install_calls==(reuse?0:1));
  if(reuse)assert(!wr_assoc_event_entry_current(&ad,&event,entry));
 }
 puts("native GTK request: stale hardware write refused, earlier software mutation witness remains");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-assoc-gtk-gap-') as temp:
    d=Path(temp);(d/'gap.c').write_text(prefix+actors+wrapper+main)
    subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function',
        '-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(d/'gap.c'),'-o',str(d/'gap')],check=True)
    subprocess.run([str(d/'gap')],check=True)
report={'native_group_request_body_sha256':hashlib.sha256(body.encode()).hexdigest(),
    'source_sha256':hashlib.sha256(source.encode()).hexdigest(),
    'actual_native_group_request_executed':True,'reuse_after_dispatch_injected_by_host_actor':True,
    'stale_hardware_key_write_refused':True,'stale_software_gtk_mutation_witness':True,
    'new_association_handshake_actor_called':True,'execution_gap_closed':False,
    'source_file_sha256':hashlib.sha256((a.source/'common/cmm_wpa.c').read_bytes()).hexdigest(),
    'composed_group_block_sha256':hashlib.sha256(body.encode()).hexdigest(),
    'crypto_timers_dma_hardware_modeled':False,'target_compiled':False,'runtime_verified':False}
if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
