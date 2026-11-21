#!/usr/bin/env python3
"""Execute new Linux admission helper with actual receipt and owner predicates."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args();here=Path(__file__).resolve().parent
# Reuse the reviewed GTK fixture boundary adapter setup, not its test runner.
# Run only its pure source assembly up to the executable fixture block. Replace
# argument parsing with a fixed pinned source and stop before invoking gcc.
source=(here/'check-ra2-gtk-request.py').read_text()
prefix_code=source[:source.index("with tempfile.TemporaryDirectory(prefix='wr-ra2-gtk-scope-')")]
fixed=str(a.source.resolve(strict=True))
# Obtain the assembly through its exact statements with a controlled argv.
import sys
old=sys.argv;sys.argv=[str(here/'check-ra2-gtk-request.py'),fixed]
ns={'__file__':str(here/'check-ra2-gtk-request.py'),'__name__':'fixture_definitions'}
try:exec(compile(prefix_code,str(here/'check-ra2-gtk-request.py'),'exec'),ns)
finally:sys.argv=old
prefix=ns['prefix'].replace('struct wr_iot_peer_table_owner wr_iot_peer_table_owner;',
 'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')
prefix=prefix.replace('#include "peer-table-owner.h"','#include "peer-table-owner.h"\n#include "ra2-association-owner.h"')
setup=ns['main'][:ns['main'].index('int main(void){')]
actors=ns['actors']
# setup references the GTK fixture counters, which are harmless here; do not
# execute its native key actors. Only admission/leave and actual receipt code.
module=__import__('runpy').run_path(str(here/'ra2-mutation-wrappers.py'))
wrappers='static unsigned native_mutation_calls;\n'
for name,sites in module['SITES'].items():
 _,receipts=module['compose'](name,(a.source/name).read_text())
 for (function,static,reassoc),(wrapper,_) in zip(sites,receipts):
  outer=wrapper[:wrapper.rindex('static VOID wr_ra2_native_')]
  arguments='RTMP_ADAPTER *pAd,MLME_QUEUE_ELEM *Elem'+(',BOOLEAN isReassoc' if reassoc else '')
  body='(void)pAd;(void)Elem;'+('(void)isReassoc;' if reassoc else '')+'native_mutation_calls++;return;'
  wrappers+=outer+'static VOID wr_ra2_native_'+function+'('+arguments+'){'+body+'}\n'
insertion_compose=__import__('runpy').run_path(str(here/'ra2-mutation-binding.py'))['compose_insertion']
insertion=insertion_compose((here/'peer-normal-insert.inc').read_text())
insertion_actor=r'''
static unsigned insert_calls;static int insert_failure;
static MAC_TABLE_ENTRY *wr_iot_mac_insert_entry(RTMP_ADAPTER *ad,UCHAR *addr,
 struct wifi_dev *wdev,UINT32 type,UCHAR mode,BOOLEAN clean,const void *token,unsigned long serial){
 (void)addr;(void)type;(void)mode;(void)clean;(void)token;(void)serial;insert_calls++;
 if(wdev==&ad->ApCfg.MBSSID[2].wdev){
  assert(ad->wr_ra2_assoc_owner.associations==1&&ad->wr_iot_control_users==1);
 }
 assert(ad->wr_iot_peer_table_owner.transactions==1&&!ad->MacTabLock.held);
 return insert_failure?NULL:&ad->MacTab.Content[1];
}
'''
unit=prefix+actors+'\n#include "ra2-mutation-admission-kernel.h"\n'+wrappers+insertion_actor+insertion+setup+r'''


int main(void){
 RTMP_ADAPTER ad,other;MLME_QUEUE_ELEM event,other_event;
 struct wr_ra2_assoc_ticket ticket={0},foreign={0},key={0};
 /* Execute each exact generated outer wrapper together with actual Linux
  * admission. Native bodies are early-return boundary actors, not SDK models. */
 for(unsigned selected=0;selected<3;selected++){
  for(unsigned refused=0;refused<2;refused++){
   setup(&ad,&event,2);native_mutation_calls=0;
   ad.wr_iot_ra2_key_active=refused;
   if(selected==0)ap_cmm_peer_assoc_req_action(&ad,&event,1);
   if(selected==1)APPeerAuthReqAtIdleAction(&ad,&event);
   if(selected==2)APPeerAuthConfirmAction(&ad,&event);
   assert(native_mutation_calls==!refused);
   assert(!ad.wr_iot_control_users&&!ad.wr_ra2_assoc_owner.associations);
   assert(!ad.wr_iot_control_poisoned);
  }
 }
 setup(&ad,&event,2);
 assert(wr_ra2_mutation_enter_wdev(&ad,&ad.ApCfg.MBSSID[2].wdev,&ticket)==1);
 assert(ad.wr_ra2_assoc_owner.associations==1&&ad.wr_iot_control_users==1);
 assert(!wr_ra2_assoc_enter(&ad.wr_ra2_assoc_owner,&key,1));
 wr_ra2_mutation_leave(&ad,&ticket);
 ad.wr_iot_ra2_key_active=1;
 assert(wr_ra2_mutation_enter_wdev(&ad,&ad.ApCfg.MBSSID[2].wdev,&ticket)==-1);
 assert(wr_ra2_mutation_enter_wdev(&ad,&ad.ApCfg.MBSSID[1].wdev,&ticket)==0);
 assert(!ticket.active&&!ad.wr_iot_control_users);
 for(unsigned failure=0;failure<2;failure++){
  unsigned char addr[6]={9};setup(&ad,&event,2);insert_calls=0;insert_failure=failure;
  MAC_TABLE_ENTRY *result=MacTableInsertEntry(&ad,addr,&ad.ApCfg.MBSSID[2].wdev,1,1,1);
  assert(insert_calls==1&&(result!=NULL)==!failure);
  assert(!ad.wr_ra2_assoc_owner.associations&&!ad.wr_iot_control_users&&!ad.wr_iot_peer_table_owner.transactions);
  ad.wr_iot_ra2_key_active=1;insert_calls=0;
  assert(!MacTableInsertEntry(&ad,addr,&ad.ApCfg.MBSSID[2].wdev,1,1,1)&&!insert_calls);
  insert_failure=0;
  assert(MacTableInsertEntry(&ad,addr,&ad.ApCfg.MBSSID[1].wdev,1,1,1));
  assert(insert_calls==1&&!ad.wr_iot_control_users&&!ad.wr_ra2_assoc_owner.associations);
 }
 setup(&ad,&event,2);ad.wr_iot_control_users=3;
 assert(wr_ra2_mutation_enter(&ad,&event,&ticket)==1);
 assert(ad.wr_iot_control_users==4&&ad.wr_ra2_assoc_owner.associations==1);
 assert(!wr_ra2_assoc_enter(&ad.wr_ra2_assoc_owner,&key,1));
 wr_ra2_mutation_leave(&ad,&ticket);
 assert(ad.wr_iot_control_users==3&&!ad.wr_ra2_assoc_owner.associations);
 for(unsigned fault=0;fault<6;fault++){
  setup(&ad,&event,2);ticket=(struct wr_ra2_assoc_ticket){0};
  if(fault==0)ad.wr_iot_driver_owner.receipt.valid=0;
  if(fault==1)ad.wr_iot_ra2_key_active=1;
  if(fault==2)ad.wr_ra2_assoc_owner.key_active=1;
  if(fault==3)ad.wr_ra2_assoc_owner.serial=~0UL;
  if(fault==4)ad.wr_iot_close_owner.active=1;
  if(fault==5)event.MsgLen=3;
  assert(wr_ra2_mutation_enter(&ad,&event,&ticket)==-1);
  assert(!ticket.active&&!ad.wr_iot_control_users&&!ad.wr_ra2_assoc_owner.associations);
 }
 setup(&ad,&event,1);ad.wr_iot_driver_owner.receipt.valid=0;
 assert(wr_ra2_mutation_enter(&ad,&event,&ticket)==0&&!ticket.active);
 setup(&ad,&event,2);ad.mt=0;
 assert(wr_ra2_mutation_enter(&ad,&event,&ticket)==0&&!ticket.active);
 setup(&ad,&event,2);setup(&other,&other_event,2);
 assert(wr_ra2_mutation_enter(&ad,&event,&ticket)==1);
 assert(wr_ra2_mutation_enter(&other,&other_event,&foreign)==1);
 wr_ra2_mutation_leave(&ad,&foreign);
 assert(ad.wr_iot_control_poisoned&&ad.wr_iot_control_users==1);
 assert(other.wr_iot_control_users==1&&foreign.active);
 wr_ra2_mutation_leave(&other,&foreign);
 assert(!other.wr_iot_control_users);
 puts("ra2 Linux mutation admission: actual receipt/owner predicates host PASS; no target acceptance");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-mutation-admit-') as temp:
 d=Path(temp);(d/'check.c').write_text(unit)
 for abl in (False,True):
  flags=['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']
  if abl:flags+=['-DOS_ABL_FUNC_SUPPORT=1']
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/'check.c'),'-o',str(d/'check')],check=True)
  subprocess.run([str(d/'check')],check=True)
