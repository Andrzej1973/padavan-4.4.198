#!/usr/bin/env python3
"""Execute exact per-ra2 peer scope with native deletion wrapper and SDK actors."""
import argparse,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
source=(here/'check-ra2-gtk-request.py').read_text()
source=source[:source.index("with tempfile.TemporaryDirectory(prefix='wr-ra2-gtk-scope-')")]
old=sys.argv;sys.argv=[str(here/'check-ra2-gtk-request.py'),str(a.source.resolve(strict=True))]
ns={'__file__':str(here/'check-ra2-gtk-request.py'),'__name__':'fixture_definitions'}
try:exec(compile(source,str(here/'check-ra2-gtk-request.py'),'exec'),ns)
finally:sys.argv=old
setup=ns['main'][:ns['main'].index('int main(void){')]
unit=ns['prefix']+ns['actors']+'\n#include "ra2-rekey-peer-scope.h"\n'+setup+r'''
int main(void){
 RTMP_ADAPTER ad;MLME_QUEUE_ELEM event;struct wr_ra2_rekey_peer_scope scope;
 setup(&ad,&event,2);expect_scoped=0;
 ad.MacTab.Content[2]=ad.MacTab.Content[1];ad.MacTab.Content[2].wcid=2;
 ad.MacTab.Content[3]=ad.MacTab.Content[1];ad.MacTab.Content[3].wcid=3;
 ad.MacTab.Content[3].func_tb_idx=1;ad.MacTab.Content[3].wdev=&ad.ApCfg.MBSSID[1].wdev;
 assert(wr_ra2_rekey_peers_enter(&ad,&scope));
 assert(scope.active&&scope.generations[1]==1&&scope.generations[2]==1&&!scope.generations[3]);
 assert(ad.wr_assoc_event_users[1]==1&&ad.wr_assoc_event_users[2]==1&&!ad.wr_assoc_event_users[3]);
 assert(ad.wr_iot_peer_table_owner.transactions==1&&!ad.MacTabLock.held);
 assert(!wr_assoc_reassociate(&ad,&ad.MacTab.Content[1]));
 assert(!wr_iot_mac_delete_entry(&ad,1,ad.MacTab.Content[1].Addr,NULL,0,0,0)&&!deletes);
 assert(!wr_iot_peer_table_begin(&ad.wr_iot_peer_table_owner));
 assert(wr_ra2_rekey_peers_leave(&ad,&scope));
 assert(!scope.active&&!ad.wr_iot_peer_table_owner.transactions);
 assert(!ad.wr_assoc_event_users[1]&&!ad.wr_assoc_event_users[2]);
 assert(wr_assoc_reassociate(&ad,&ad.MacTab.Content[1]));
 assert(!wr_ra2_rekey_peers_leave(&ad,&scope));
 for(unsigned fault=0;fault<5;fault++){
  setup(&ad,&event,2);
  if(fault==0)ad.wr_iot_peer_delete_active=1;
  if(fault==1)ad.wr_iot_peer_table_owner.transactions=1;
  if(fault==2)ad.wr_assoc_event_users[1]=1;
  if(fault==3)ad.MacTab.Content[1].assoc_gen=0;
  if(fault==4)NdisAcquireSpinLock(&ad.MacTabLock);
  assert(!wr_ra2_rekey_peers_enter(&ad,&scope));
  assert(!scope.active&&!scope.generations[1]);
  assert(ad.wr_iot_peer_table_owner.transactions==(fault==1?1U:0U));
  assert(ad.wr_assoc_event_users[1]==(fault==2?1U:0U));
  if(fault==4)NdisReleaseSpinLock(&ad.MacTabLock);
 }
 setup(&ad,&event,2);assert(wr_ra2_rekey_peers_enter(&ad,&scope));
 ad.MacTab.Content[1].assoc_gen++;
 assert(!wr_ra2_rekey_peers_leave(&ad,&scope));
 assert(ad.wr_assoc_event_users[1]==1&&ad.wr_iot_peer_table_owner.poisoned);
 puts("ra2 periodic peer retention: helper host PASS; callback checked separately");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-rekey-peers-') as temp:
 d=Path(temp);(d/'check.c').write_text(unit)
 for abl in (False,True):
  flags=[]
  if abl:flags=['-DOS_ABL_FUNC_SUPPORT=1']
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/'check.c'),'-o',str(d/'check')],check=True)
  subprocess.run([str(d/'check')],check=True)
