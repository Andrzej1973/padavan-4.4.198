#!/usr/bin/env python3
"""Run the composed native GTK request with real admission and deletion guards."""
import argparse,ast,hashlib,json,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('--prepared-driver',type=Path);p.add_argument('--output',type=Path)
a=p.parse_args();here=Path(__file__).resolve().parent
texts=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)
compose=runpy.run_path(str(here/'ra2-gtk-request-composition.py'))['compose']
source=compose(texts['common/cmm_wpa.c'])
if a.prepared_driver:
 assert (a.prepared_driver/'common/cmm_wpa.c').read_text()==source
 assert (a.prepared_driver/'include/ra2-gtk-request-kernel.h').read_text()==(here/'ra2-gtk-request-kernel.h').read_text()
assert source.count('wr_iot_ra2_group_request(pAd,Elem,pEntry);')==1
assert source.count('static VOID WpaEAPOLKeyAction(')==1
assert 'static \n#ifdef' not in source
try:compose(source)
except ValueError:pass
else:raise AssertionError('duplicate binding accepted')
start=source.index('static VOID wr_iot_ra2_group_request_raw(')
helpers=source[start:source.index('\n#endif\nVOID WpaEAPOLKeyAction(',start)]
tree=ast.parse((here/'check-assoc-generation.py').read_text())
prefix=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='prefix' for t in n.targets)]
assert len(prefix)==1;prefix=prefix[0]
prefix=prefix.replace('unsigned assoc_gen,wcid;', 'unsigned assoc_gen,wcid;struct wifi_dev *wdev;int WpaState,GTKState,ReTryCounter;unsigned char func_tb_idx;')
insert=r'''
#include "ra2-rekey-admission.h"
#include "driver-api-close-admission.h"
#include "peer-table-owner.h"
#define VOID void
typedef unsigned char UCHAR,UINT8;
typedef unsigned short USHORT;
typedef int INT32;
#define RT_DEBUG_TRACE 0
#define DBGPRINT(level,args) do{}while(0)
#define LEN_TKIP_GTK 32
#define AS_PTKINITDONE 5
#define REKEY_NEGOTIATING 6
#define GROUP_MSG1_RETRY_TIMER_CTR 7
#define IS_ENTRY_CLIENT(e) ((e)->valid)
#define GET_GroupKey_WCID(ad,wcid,idx) do{(void)(ad);(wcid)=100+(idx);}while(0)
#define WDEV_NUM_MAX 3
#define MAX_LEN_OF_TR_TABLE 4
#define IS_MT7603(ad) ((ad)->mt)
#define VIRTUAL_IF_NUM(ad) ((ad)->vendor_count)
struct wifi_dev {unsigned char bssid[6];void *if_dev;unsigned GroupKeyWepStatus,DefaultKeyId;};
typedef struct {struct wifi_dev wdev;unsigned char GMK[32],GNonce[32],GTK[32];} BSS_STRUCT;
'''
prefix=prefix.replace('typedef struct {struct lock MacTabLock;',insert+'''typedef struct {struct lock MacTabLock;
 int mt,vendor_count;struct lock wr_iot_transition_lock;
 unsigned wr_iot_ra2_key_active,wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed,wr_iot_peer_delete_active;
 struct {int active;} wr_iot_close_owner,wr_iot_closed_probe;
 struct {int idle;} wr_iot_peer_close_executor;
 struct wr_iot_peer_table_owner wr_iot_peer_table_owner;
 struct wr_iot_driver_owner wr_iot_driver_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
 void *net_dev;
 struct {unsigned BssidNum;BSS_STRUCT MBSSID[3];} ApCfg;''')
actors=r'''
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(flags);NdisAcquireSpinLock(lock);}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(flags);NdisReleaseSpinLock(lock);}while(0)
static int deletes,randoms,installs,handshakes,expect_scoped,force_early_return;
static MLME_QUEUE_ELEM *active_event;
static int wr_iot_peer_close_executor_idle(void *p){(void)p;return 1;}
static BOOLEAN wr_iot_mac_delete_entry_body(RTMP_ADAPTER *ad,USHORT wcid,UCHAR *addr,const void *dev,unsigned long gen,unsigned long resume,unsigned long serial){
 (void)ad;(void)wcid;(void)addr;(void)dev;(void)gen;(void)resume;(void)serial;deletes++;return TRUE;
}
#include "peer-delete-execution.inc"
'''
actors+=(here/'mcu-control-admission.inc').read_text()
actors+=r'''
#include "ra2-gtk-request-kernel.h"
static void GenRandom(RTMP_ADAPTER *ad,unsigned char *bssid,unsigned char *nonce){
 (void)bssid;randoms++;memset(nonce,0x51,32);
 if(force_early_return)active_event->assoc_gen=0;
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(expect_scoped){
  MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[1];
  assert(ad->wr_iot_control_users==1&&ad->wr_iot_ra2_key_active==1);
  assert(ad->wr_iot_peer_table_owner.transactions==1&&ad->wr_assoc_event_users[1]==1);
  assert(!wr_assoc_reassociate(ad,entry));
  assert(!wr_iot_mac_delete_entry(ad,1,entry->Addr,NULL,0,0,0));assert(!deletes);
  assert(!wr_iot_peer_table_begin(&ad->wr_iot_peer_table_owner));
  struct wr_iot_driver_open_receipt *r=&ad->wr_iot_driver_owner.receipt;
  assert(!wr_iot_driver_close_admissible(&ad->wr_iot_driver_owner,r->request_id,
   &ad->wr_iot_transition,ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,
   ad->ApCfg.MBSSID[2].wdev.if_dev,r->epoch,r->generation,r->open_token,
   ad->vendor_count,ad->wr_iot_control_users,0,0));
  struct wr_iot_ra2_gtk_request_scope other;MLME_QUEUE_ELEM event={0};
  assert(!wr_iot_ra2_gtk_request_enter(ad,&event,entry,&other));
  assert(ad->wr_iot_control_users==1&&!other.active);
 }
#endif
}
static void WpaDeriveGTK(unsigned char *gmk,unsigned char *nonce,unsigned char *bssid,unsigned char *gtk,unsigned len){
 (void)gmk;(void)nonce;(void)bssid;assert(len==32);memset(gtk,0x72,len);
}
static void WPAStart2WayGroupHS(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){
 (void)ad;assert(entry->assoc_gen==1);handshakes++;
}
static void WPAInstallSharedKey(RTMP_ADAPTER *ad,unsigned cipher,unsigned idx,unsigned key,unsigned wcid,int tx,unsigned char *gtk,unsigned len){
 (void)ad;(void)cipher;(void)tx;(void)gtk;assert(idx<3&&key==2&&wcid==100+idx&&len==32);installs++;
}
'''
main=r'''
static int main_dev,iot_dev;
static void setup(RTMP_ADAPTER *ad,MLME_QUEUE_ELEM *event,unsigned bss){
 memset(ad,0,sizeof(*ad));memset(event,0,sizeof(*event));
 ad->mt=1;ad->vendor_count=2;ad->ApCfg.BssidNum=3;ad->net_dev=&main_dev;
 ad->MacTabLock.pContent=&ad->MacTabLock;
 ad->ApCfg.MBSSID[2].wdev.if_dev=&iot_dev;
 ad->ApCfg.MBSSID[2].wdev.bssid[0]=2;ad->ApCfg.MBSSID[1].wdev.bssid[0]=1;
 wr_iot_peer_table_owner_init(&ad->wr_iot_peer_table_owner);
 wr_iot_radio_transition_init(&ad->wr_iot_transition);
 ad->wr_iot_transition.phase=WR_RADIO_READY;ad->wr_iot_transition.main_ready=1;
 unsigned long sequence=0;
 struct wr_iot_interface_ref *m=wr_iot_registry_add_family(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
 struct wr_iot_interface_ref *r=wr_iot_registry_add_family(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
 assert(m&&r);m->published=r->published=1;m->phase=r->phase=WR_REF_OWNED;m->last_token=1;r->last_token=2;
 struct wr_iot_driver_open_receipt *receipt=&ad->wr_iot_driver_owner.receipt;
 receipt->device=&iot_dev;receipt->epoch=ad->wr_iot_transition.epoch;receipt->generation=r->generation;
 receipt->open_token=2;receipt->valid=receipt->first_beacon_confirmed=1;receipt->request_id[0]=1;
 MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[1];entry->valid=1;entry->wcid=1;
 entry->func_tb_idx=bss;entry->wdev=&ad->ApCfg.MBSSID[bss].wdev;entry->WpaState=AS_PTKINITDONE;entry->Addr[0]=9;
 ad->wr_assoc_generations[1]=entry->assoc_gen=1;wr_assoc_publish_slot_locked(ad,entry);
 struct wr_assoc_stamp stamp=wr_assoc_capture(ad,1,6,entry->Addr,1);wr_assoc_publish(event,&stamp);
 event->Machine=1;event->MsgLen=24;COPY_MAC_ADDR(((PHEADER_802_11)event->Msg)->Addr1,entry->wdev->bssid);
 ad->ApCfg.MBSSID[bss].wdev.DefaultKeyId=1;
 deletes=randoms=installs=handshakes=force_early_return=0;active_event=event;
}
int main(void){
 RTMP_ADAPTER ad;MLME_QUEUE_ELEM event;
 setup(&ad,&event,2);expect_scoped=1;
 wr_iot_ra2_group_request(&ad,&event,&ad.MacTab.Content[1]);
 assert(randoms==1&&handshakes==1&&installs==1);
 assert(!ad.wr_iot_control_users&&!ad.wr_iot_ra2_key_active&&!ad.wr_assoc_event_users[1]);
 assert(!ad.wr_iot_peer_table_owner.transactions&&!ad.wr_iot_control_poisoned);
 assert(wr_assoc_reassociate(&ad,&ad.MacTab.Content[1]));
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 /* Closed, stale, contended, deleting and already-active scope all refuse
  * before native nonce/key/peer mutation and release any partial admission. */
 for(unsigned which=0;which<8;which++){
  setup(&ad,&event,2);
  if(which==0)ad.wr_iot_driver_owner.receipt.valid=0;
  if(which==1){ad.wr_assoc_generations[1]=2;ad.MacTab.Content[1].assoc_gen=2;wr_assoc_publish_slot_locked(&ad,&ad.MacTab.Content[1]);}
  if(which==2)NdisAcquireSpinLock(&ad.MacTabLock);
  if(which==3)ad.wr_iot_peer_delete_active=1;
  if(which==4)ad.wr_iot_ra2_key_active=1;
  if(which==5)ad.wr_iot_peer_table_owner.active=1;
  if(which==6)ad.MacTab.Content[1].Addr[0]^=1;
  if(which==7)((PHEADER_802_11)event.Msg)->Addr1[0]=1;
  wr_iot_ra2_group_request(&ad,&event,&ad.MacTab.Content[1]);
  assert(!randoms&&!installs&&!handshakes&&!ad.wr_iot_control_users);
  assert(!ad.wr_assoc_event_users[1]&&!ad.wr_iot_peer_table_owner.transactions);
  if(which==2)NdisReleaseSpinLock(&ad.MacTabLock);
  if(which!=4)assert(!ad.wr_iot_ra2_key_active);
 }
#endif
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 setup(&ad,&event,2);expect_scoped=1;force_early_return=1;
 wr_iot_ra2_group_request(&ad,&event,&ad.MacTab.Content[1]);
 assert(randoms==1&&!installs&&!ad.wr_iot_control_users&&!ad.wr_iot_ra2_key_active);
 assert(!ad.wr_assoc_event_users[1]&&!ad.wr_iot_peer_table_owner.transactions&&!ad.wr_iot_control_poisoned);
#endif
 setup(&ad,&event,2);ad.mt=0;expect_scoped=0;ad.wr_iot_driver_owner.receipt.valid=0;
 wr_iot_ra2_group_request(&ad,&event,&ad.MacTab.Content[1]);
 assert(randoms==1&&installs==1&&!ad.wr_iot_control_users&&!ad.wr_assoc_event_users[1]);
 setup(&ad,&event,1);expect_scoped=0;ad.wr_iot_driver_owner.receipt.valid=0;
 wr_iot_ra2_group_request(&ad,&event,&ad.MacTab.Content[1]);
 assert(randoms==1&&installs==1&&!ad.wr_iot_control_users&&!ad.wr_assoc_event_users[1]);
 puts("ra2 native GTK request scope: lifecycle mutation refused, key operation balanced; SDK actors only");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-gtk-scope-') as temp:
 d=Path(temp);(d/'scope.c').write_text(prefix+actors+helpers+main)
 for flags in ([],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT'],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT','-DOS_ABL_FUNC_SUPPORT=1']):
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/'scope.c'),'-o',str(d/'scope')],check=True)
  subprocess.run([str(d/'scope')],check=True)
report={'candidate_source_sha256':hashlib.sha256(source.encode()).hexdigest(),'host_native_group_request_verified':True,
 'guarded_reassociation_and_native_delete_refused':True,'close_refused_during_request':True,
 'competing_key_request_refused':True,'release_balanced':True,'main_guest_native_passthrough_host_checked':True,
 'target_compiled':False,'runtime_verified':False,'all_wpa_actions_lifetime_verified':False}
if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
