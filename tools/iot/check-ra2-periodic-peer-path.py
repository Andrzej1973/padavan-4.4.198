#!/usr/bin/env python3
"""Execute the actual vendor timer with key arbitration and retained peer scope."""
import argparse,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
code=(here/'check-ra2-gtk-request.py').read_text();code=code[:code.index("with tempfile.TemporaryDirectory(prefix='wr-ra2-gtk-scope-')")]
old=sys.argv;sys.argv=[str(here/'check-ra2-gtk-request.py'),str(a.source.resolve(strict=True))]
ns={'__file__':str(here/'check-ra2-gtk-request.py'),'__name__':'fixture_definitions'}
try:exec(compile(code,str(here/'check-ra2-gtk-request.py'),'exec'),ns)
finally:sys.argv=old
prefix=ns['prefix'].replace('#include "peer-table-owner.h"',
 '#include "peer-table-owner.h"\n#include "ra2-association-owner.h"')
prefix=prefix.replace('struct wr_iot_peer_table_owner wr_iot_peer_table_owner;',
 'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')
prefix=prefix.replace('unsigned GroupKeyWepStatus,DefaultKeyId;', 'unsigned AuthMode,GroupKeyWepStatus,DefaultKeyId;')
prefix=prefix.replace('typedef struct {struct wifi_dev wdev;unsigned char GMK[32],GNonce[32],GTK[32];} BSS_STRUCT;',
 '''typedef int RALINK_TIMER_STRUCT,*PRALINK_TIMER_STRUCT;
 typedef unsigned int UINT;
 #define TIME_REKEY 1
 #define PKT_REKEY 2
 #define Ndis802_11AuthModeWPA 3
 #define Ndis802_11AuthModeWPA1PSKWPA2PSK 9
 typedef struct {struct wifi_dev wdev;unsigned char GMK[32],GNonce[32],GTK[32];
 int REKEYTimer;struct {int ReKeyMethod;unsigned long ReKeyInterval;} WPAREKEY;
 unsigned long REKEYCOUNTER;unsigned RekeyCountDown,StaCount;} BSS_STRUCT;''')
setup=ns['main'][:ns['main'].index('int main(void){')]
actors=ns['actors'].replace('assert(ad->wr_iot_control_users==1&&ad->wr_iot_ra2_key_active==1);',
 'assert(ad->wr_iot_control_users==1&&ad->wr_iot_ra2_key_active==1);\n'
 '  assert(ad->wr_ra2_assoc_owner.key_active&&!ad->wr_ra2_assoc_owner.associations);\n'
 '  struct wr_ra2_assoc_ticket other_mutation={0};\n'
 '  assert(!wr_ra2_assoc_enter(&ad->wr_ra2_assoc_owner,&other_mutation,0));')
source=(a.source/'ap/ap_wpa.c').read_text();start=source.index('VOID GREKEYPeriodicExec(')
native=source[start:source.index('\n}',start)+2]
wrapped=runpy.run_path(str(here/'ra2-rekey-composition.py'))['compose'](native)
key=runpy.run_path(str(here/'ra2-key-arbitration-composition.py'))
wrapped=key['periodic_peer_scope'](key['periodic'](wrapped))
main=r'''
static void timer_setup(RTMP_ADAPTER *ad,MLME_QUEUE_ELEM *event){
 setup(ad,event,2);expect_scoped=1;
 for(unsigned i=0;i<3;i++){
  BSS_STRUCT *b=&ad->ApCfg.MBSSID[i];b->wdev.AuthMode=7;
  b->WPAREKEY.ReKeyMethod=TIME_REKEY;b->WPAREKEY.ReKeyInterval=100;
  b->wdev.DefaultKeyId=1;
 }
}
int main(void){
 RTMP_ADAPTER ad;MLME_QUEUE_ELEM event;
 timer_setup(&ad,&event);
 ad.ApCfg.MBSSID[2].StaCount=1;ad.ApCfg.MBSSID[2].REKEYCOUNTER=100;
 GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
 assert(randoms==1&&handshakes==1&&!installs);
 assert(ad.MacTab.Content[1].assoc_gen==1&&ad.MacTab.Content[1].GTKState==REKEY_NEGOTIATING);
 assert(!ad.wr_assoc_event_users[1]&&!ad.wr_iot_peer_table_owner.transactions);
 assert(!ad.wr_iot_control_users&&!ad.wr_iot_ra2_key_active&&!ad.wr_ra2_assoc_owner.key_active);
 assert(!ad.wr_iot_control_poisoned&&wr_assoc_reassociate(&ad,&ad.MacTab.Content[1]));
 /* Actual countdown/key install path also balances retained peers. */
 timer_setup(&ad,&event);ad.ApCfg.MBSSID[2].RekeyCountDown=1;
 ad.ApCfg.MBSSID[2].wdev.DefaultKeyId=2;
 GREKEYPeriodicExec(NULL,&ad,NULL,&ad.ApCfg.MBSSID[2].REKEYTimer);
 assert(installs==1&&!randoms&&!handshakes);
 assert(!ad.wr_iot_control_users&&!ad.wr_assoc_event_users[1]);
 for(unsigned fault=0;fault<5;fault++){
  timer_setup(&ad,&event);BSS_STRUCT *b=&ad.ApCfg.MBSSID[2];
  b->StaCount=1;b->REKEYCOUNTER=100;b->RekeyCountDown=1;
  if(fault==0)ad.wr_iot_peer_delete_active=1;
  if(fault==1)ad.wr_iot_peer_table_owner.transactions=1;
  if(fault==2)ad.wr_assoc_event_users[1]=1;
  if(fault==3)NdisAcquireSpinLock(&ad.MacTabLock);
  if(fault==4)ad.wr_ra2_assoc_owner.associations=1;
  GREKEYPeriodicExec(NULL,&ad,NULL,&b->REKEYTimer);
  assert(!randoms&&!handshakes&&!installs&&b->REKEYCOUNTER==100&&b->RekeyCountDown==1);
  assert(!ad.wr_iot_control_users&&!ad.wr_iot_ra2_key_active&&!ad.wr_ra2_assoc_owner.key_active);
  assert(ad.wr_iot_peer_table_owner.transactions==(fault==1));
  assert(ad.wr_assoc_event_users[1]==(fault==2));
  if(fault==3)NdisReleaseSpinLock(&ad.MacTabLock);
 }
 puts("actual native periodic callback with retained peers: host PASS; no device acceptance");return 0;
}
'''
unit=prefix+actors+wrapped+setup+main
with tempfile.TemporaryDirectory(prefix='wr-ra2-periodic-peers-') as temp:
 d=Path(temp);(d/'test.c').write_text(unit)
 for abl in (False,True):
  flags=['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT','-DCONFIG_AP_SUPPORT']
  if abl:flags+=['-DOS_ABL_FUNC_SUPPORT=1']
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/'test.c'),'-o',str(d/'test')],check=True)
  subprocess.run([str(d/'test')],check=True)
