"""Execute actual native and scoped GTK timer bodies with SDK boundary actors."""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import subprocess
import tempfile

HERE = Path(__file__).resolve().parent
PREFIX = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "ra2-rekey-admission.h"
#include "driver-api-close-admission.h"
#define VOID void
#define IN
typedef void *PVOID;
typedef unsigned int UINT;
typedef unsigned long ULONG;
typedef unsigned short USHORT;
typedef unsigned char UCHAR;
typedef int INT32;
typedef int RALINK_TIMER_STRUCT,*PRALINK_TIMER_STRUCT;
#define TIME_REKEY 1
#define PKT_REKEY 2
#define Ndis802_11AuthModeWPA 3
#define Ndis802_11AuthModeWPA1PSKWPA2PSK 9
#define MAX_LEN_OF_MAC_TABLE 4
#define AS_PTKINITDONE 5
#define REKEY_NEGOTIATING 6
#define GROUP_MSG1_RETRY_TIMER_CTR 7
#define LEN_TKIP_GTK 32
#define TRUE 1
#define WDEV_NUM_MAX 3
#define DBGPRINT(level,args) do{}while(0)
#define IS_ENTRY_CLIENT(entry) ((entry)->type==1)
#define IS_MT7603(ad) ((ad)->mt)
#define VIRTUAL_IF_NUM(ad) ((ad)->vendor_count)
#define GET_GroupKey_WCID(ad,wcid,index) do{(void)(ad);(wcid)=100+(index);}while(0)
typedef struct {int type,WpaState,GTKState,ReTryCounter;unsigned assoc_gen;unsigned char func_tb_idx;} MAC_TABLE_ENTRY;
struct wifi_dev {unsigned AuthMode,DefaultKeyId,GroupKeyWepStatus;void *if_dev;unsigned char bssid[6];};
typedef struct {
 int REKEYTimer;struct wifi_dev wdev;
 struct {int ReKeyMethod;unsigned long ReKeyInterval;} WPAREKEY;
 unsigned long REKEYCOUNTER;unsigned RekeyCountDown,StaCount;
 unsigned char GMK[32],GNonce[32],GTK[32];
} BSS_STRUCT;
typedef struct {
 int mt,vendor_count,wr_iot_transition_lock;
 struct {unsigned BssidNum;BSS_STRUCT MBSSID[4];} ApCfg;
 struct {MAC_TABLE_ENTRY Content[MAX_LEN_OF_MAC_TABLE];} MacTab;
 struct wr_iot_driver_owner wr_iot_driver_owner;
 struct wr_iot_radio_transition wr_iot_transition;
 struct wr_iot_interface_ref wr_iot_interface_refs[WDEV_NUM_MAX+1];
 void *net_dev;
 unsigned wr_iot_ra2_key_active,wr_iot_control_users,wr_iot_control_poisoned,wr_iot_boot_active,wr_iot_boot_failed;
 struct {int active;} wr_iot_close_owner,wr_iot_closed_probe;
} RTMP_ADAPTER,*PRTMP_ADAPTER;
static unsigned locks,installs,derivations,handshakes,randoms;
static int native_case,replace_peer_in_nonce;
static unsigned handshake_generation;
#define RTMP_IRQ_LOCK(lock,flags) do{(void)(lock);(void)(flags);assert(!locks);locks++;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(lock);(void)(flags);assert(locks==1);locks--;}while(0)
static void GenRandom(RTMP_ADAPTER *ad,unsigned char *bssid,unsigned char *nonce){
 (void)bssid;assert(!locks);memset(nonce,1,32);randoms++;
 /* SDK boundary actor: emulate WCID reuse after timer admission and before
  * its peer loop. This does not emulate a device or actual deletion code. */
 if(replace_peer_in_nonce){
  MAC_TABLE_ENTRY *entry=&ad->MacTab.Content[1];
  memset(entry,0,sizeof(*entry));entry->type=1;entry->WpaState=AS_PTKINITDONE;
  entry->func_tb_idx=2;entry->assoc_gen=2;
 }
}
static void WpaDeriveGTK(unsigned char *gmk,unsigned char *nonce,unsigned char *bssid,unsigned char *gtk,unsigned length){(void)gmk;(void)nonce;(void)bssid;assert(!locks&&length==32);memset(gtk,2,length);derivations++;}
static void WPAStart2WayGroupHS(RTMP_ADAPTER *ad,MAC_TABLE_ENTRY *entry){(void)ad;assert(!locks);handshake_generation=entry->assoc_gen;handshakes++;}
static void WPAInstallSharedKey(RTMP_ADAPTER *ad,unsigned cipher,unsigned bss,unsigned key,unsigned wcid,int ae,unsigned char *gtk,unsigned length){
 (void)cipher;(void)key;(void)gtk;assert(!locks&&bss<3&&wcid==100+bss&&ae==1&&length==32);installs++;
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(!native_case&&ad->mt&&bss==2){
  assert(ad->wr_iot_control_users);
  struct wr_iot_driver_open_receipt *r=&ad->wr_iot_driver_owner.receipt;
  assert(!wr_iot_driver_close_admissible(&ad->wr_iot_driver_owner,r->request_id,&ad->wr_iot_transition,
   ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,ad->net_dev,ad->ApCfg.MBSSID[2].wdev.if_dev,
   r->epoch,r->generation,r->open_token,ad->vendor_count,ad->wr_iot_control_users,0,0));
 }
#else
 (void)ad;(void)native_case;
#endif
}
'''
CASES = r'''
static int main_dev,iot_dev;
static void reset(RTMP_ADAPTER *ad){
 memset(ad,0,sizeof(*ad));ad->mt=1;ad->vendor_count=2;ad->ApCfg.BssidNum=3;ad->net_dev=&main_dev;
 locks=installs=derivations=handshakes=randoms=0;replace_peer_in_nonce=0;handshake_generation=0;
 wr_iot_radio_transition_init(&ad->wr_iot_transition);ad->wr_iot_transition.phase=WR_RADIO_READY;ad->wr_iot_transition.main_ready=1;
 unsigned long sequence=0;
 struct wr_iot_interface_ref *main=wr_iot_registry_add_family(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,&sequence,&main_dev,WR_REF_FAMILY_MAIN);
 struct wr_iot_interface_ref *iot=wr_iot_registry_add_family(ad->wr_iot_interface_refs,WDEV_NUM_MAX+1,&sequence,&iot_dev,WR_REF_FAMILY_MBSS);
 assert(main&&iot);main->published=iot->published=1;main->phase=iot->phase=WR_REF_OWNED;main->last_token=1;iot->last_token=2;
 struct wr_iot_driver_open_receipt *r=&ad->wr_iot_driver_owner.receipt;
 r->device=&iot_dev;r->epoch=ad->wr_iot_transition.epoch;r->generation=iot->generation;r->open_token=2;r->valid=r->first_beacon_confirmed=1;r->request_id[0]=1;
 for(unsigned i=0;i<3;i++){
  BSS_STRUCT *b=&ad->ApCfg.MBSSID[i];b->wdev.AuthMode=7;b->wdev.if_dev=i==2?&iot_dev:&main_dev;
  b->WPAREKEY.ReKeyMethod=TIME_REKEY;b->WPAREKEY.ReKeyInterval=100;b->RekeyCountDown=1;
 }
}
int main(void){
 RTMP_ADAPTER ad;reset(&ad);native_case=1;
 ad.wr_iot_interface_refs[1].phase=WR_REF_IDLE;
 native_GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
 assert(installs==1&&ad.ApCfg.MBSSID[2].RekeyCountDown==0);native_case=0;
 for(unsigned fault=0;fault<12;fault++){
  reset(&ad);
  switch(fault){
   case 1:ad.wr_iot_interface_refs[1].phase=WR_REF_IDLE;break;
   case 2:ad.wr_iot_transition.busy=WR_RADIO_BSS_CLOSE;break;
   case 3:ad.wr_iot_close_owner.active=1;break;
   case 4:ad.wr_iot_closed_probe.active=1;break;
   case 5:ad.wr_iot_boot_active=1;break;
   case 6:ad.wr_iot_control_poisoned=1;break;
   case 7:ad.wr_iot_transition.retiring=1;break;
   case 8:ad.wr_iot_driver_owner.receipt.generation++;break;
   case 9:ad.wr_iot_driver_owner.receipt.first_beacon_confirmed=0;break;
   case 10:ad.wr_iot_control_users=3;break;
   case 11:ad.wr_iot_interface_refs[1].removing=1;break;
  }
  GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
  int allowed=fault==0||fault==10;
#else
  int allowed=1;
#endif
  assert(installs==(unsigned)allowed&&!locks&&ad.wr_iot_control_users==(fault==10?3U:0U));
  assert(ad.ApCfg.MBSSID[2].REKEYCOUNTER==(unsigned)allowed&&ad.ApCfg.MBSSID[2].RekeyCountDown==(unsigned)!allowed);
 }
 for(unsigned bss=0;bss<3;bss++){
  reset(&ad);if(bss<2)ad.wr_iot_transition.busy=WR_RADIO_BSS_CLOSE;else ad.mt=0;
  GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[bss].REKEYTimer);
  assert(installs==1&&!ad.wr_iot_control_users&&!locks);
 }
 reset(&ad);ad.ApCfg.MBSSID[2].wdev.AuthMode=0;
 GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
 assert(!installs&&!ad.wr_iot_control_users&&!locks);
 /* Exercise the previously uncovered native per-peer handshake branch. */
 for(unsigned reuse=0;reuse<2;reuse++){
  reset(&ad);replace_peer_in_nonce=reuse;
  BSS_STRUCT *b=&ad.ApCfg.MBSSID[2];
  b->StaCount=1;b->REKEYCOUNTER=100;b->RekeyCountDown=0;b->wdev.DefaultKeyId=1;
  MAC_TABLE_ENTRY *entry=&ad.MacTab.Content[1];
  entry->type=1;entry->WpaState=AS_PTKINITDONE;entry->func_tb_idx=2;entry->assoc_gen=1;
  GREKEYPeriodicExec(NULL,&ad,NULL,&b->REKEYTimer);
  assert(randoms==1&&derivations==1&&handshakes==1&&!installs);
  assert(handshake_generation==(reuse?2U:1U));
  assert(entry->GTKState==REKEY_NEGOTIATING&&entry->ReTryCounter==GROUP_MSG1_RETRY_TIMER_CTR);
  assert(b->wdev.DefaultKeyId==2&&b->RekeyCountDown==2);
  assert(!ad.wr_iot_control_users&&!ad.wr_iot_ra2_key_active&&!locks);
 }
 /* A refused tick retains countdown. A later admitted native tick progresses. */
 reset(&ad);ad.wr_iot_transition.busy=WR_RADIO_BSS_CLOSE;
 GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
 ad.wr_iot_transition.busy=0;
 GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
 assert(installs==1&&!ad.wr_iot_control_users&&!locks);
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 reset(&ad);ad.wr_iot_ra2_key_active=1;
 ad.ApCfg.MBSSID[2].RekeyCountDown=1;
 GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
 assert(!installs&&!ad.wr_iot_control_users&&ad.ApCfg.MBSSID[2].RekeyCountDown==1);
 assert(ad.wr_iot_ra2_key_active==1);
#endif
 puts("PASS actual vendor GTK timer/scoped wrapper: closed countdown witness, transition/probe/identity refusal without counter mutation, admitted key install fenced against CLOSE, balanced early return, Main/Guest/other-chip passthrough and later tick progress; SDK/MMIO actors, no hardware acceptance");
}
'''


def check(root, prepared=None):
    source = (root / 'ap/ap_wpa.c').read_text()
    start = source.index('VOID GREKEYPeriodicExec(')
    native = source[start:source.index('\n}', start) + 2]
    compose = runpy.run_path(str(HERE / 'ra2-rekey-composition.py'))['compose']
    wrapped = compose(native)
    prepared_expected=compose(source)
    successor=False
    if prepared:
        if (prepared/'include/ra2-mutation-admission-kernel.h').exists():
            successor=True
            key=runpy.run_path(str(HERE/'ra2-key-arbitration-composition.py'))
            prepared_expected=key['periodic_peer_scope'](key['periodic'](prepared_expected))
        assert (prepared/'ap/ap_wpa.c').read_text() == prepared_expected
        assert (prepared/'include/ra2-rekey-admission.h').read_bytes() == (HERE/'ra2-rekey-admission.h').read_bytes()
    try:
        compose(wrapped)
    except ValueError:
        pass
    else:
        raise AssertionError('Repeated timer preparation accepted')
    control = (HERE / 'mcu-control-admission.inc').read_text()
    unit = PREFIX + control + native.replace('VOID GREKEYPeriodicExec(', 'VOID native_GREKEYPeriodicExec(', 1) + '\n' + wrapped + CASES
    with tempfile.TemporaryDirectory(prefix='wr-ra2-rekey-') as directory:
        path = Path(directory) / 'check.c';path.write_text(unit)
        for flags in ([], ['-DMT7603', '-DMT_MAC', '-DRTMP_PCI_SUPPORT']):
            binary = Path(directory) / 'check'
            subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                            '-Wno-unused-parameter', '-O2', '-fsanitize=address,undefined',
                            '-fno-pie', '-no-pie', *flags, '-I'+str(HERE), str(path), '-o', str(binary)], check=True)
            subprocess.run([str(binary)], check=True, timeout=15)
    return {'native_timer_sha256':hashlib.sha256(native.encode()).hexdigest(),
            'wrapped_timer_sha256':hashlib.sha256(wrapped.encode()).hexdigest(),
            'native_ap_wpa_sha256':hashlib.sha256(source.encode()).hexdigest(),
            'candidate_ap_wpa_sha256':hashlib.sha256(prepared_expected.encode()).hexdigest(),
            'host_control_ap_wpa_sha256':hashlib.sha256(compose(source).encode()).hexdigest(),
            'prepared_successor_arbitration_verified':successor,
            'host_execution_scope':'predecessor control callback; successor is exercised by check-ra2-periodic-peer-path.py',
            'prepared_driver_verified':bool(prepared),
            'host_contract_verified':True,'native_per_peer_branch_executed':True,
            'peer_reuse_in_nonce_boundary_actor_reaches_handshake':True,
            'periodic_peer_lifetime_verified':False,'target_verified':False,'runtime_verified':False}


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('driver',type=Path)
    parser.add_argument('--prepared-driver',type=Path)
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.output and args.output.exists():parser.error('New output required')
    result=check(args.driver,args.prepared_driver)
    if args.output:args.output.write_text(json.dumps(result,indent=2)+'\n')
