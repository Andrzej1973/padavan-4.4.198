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
prefix=ns['prefix'].replace('#include "peer-table-owner.h"', '#include "peer-table-owner.h"\n#include "ra2-association-owner.h"').replace('struct wr_iot_peer_table_owner wr_iot_peer_table_owner;', 'struct wr_iot_peer_table_owner wr_iot_peer_table_owner;struct wr_ra2_assoc_owner wr_ra2_assoc_owner;')
unit=prefix+ns['actors']+'\n#include "ra2-direct-key-scope.h"\n'+setup+r'''
int main(void){
 RTMP_ADAPTER ad,other;MLME_QUEUE_ELEM event;struct wr_ra2_direct_key_scope scope={0};
 setup(&ad,&event,2);expect_scoped=0;
 assert(wr_ra2_direct_key_enter(&ad,&scope));
 assert(ad.wr_iot_control_users==1&&ad.wr_iot_ra2_key_active&&scope.peers.active);
 assert(!wr_ra2_direct_key_enter(&ad,&scope));
 assert(!wr_assoc_reassociate(&ad,&ad.MacTab.Content[1]));
 assert(!wr_iot_mac_delete_entry(&ad,1,ad.MacTab.Content[1].Addr,NULL,0,0,0));
 assert(wr_ra2_direct_key_leave(&ad,&scope));
 assert(!ad.wr_iot_control_users&&!ad.wr_iot_ra2_key_active&&!scope.active&&!scope.peers.active);
 setup(&ad,&event,2);ad.wr_ra2_assoc_owner.associations=1;
 assert(!wr_ra2_direct_key_enter(&ad,&scope)&&!ad.wr_iot_control_users);
 setup(&ad,&event,2);ad.wr_iot_peer_table_owner.transactions=1;
 assert(!wr_ra2_direct_key_enter(&ad,&scope));
 assert(!ad.wr_iot_control_users&&!ad.wr_iot_ra2_key_active&&!scope.active);
 assert(ad.wr_iot_peer_table_owner.transactions==1);
 setup(&ad,&event,2);assert(wr_ra2_direct_key_enter(&ad,&scope));
 setup(&other,&event,2);
 assert(!wr_ra2_direct_key_leave(&other,&scope));
 assert(scope.active&&ad.wr_iot_control_users==1&&ad.wr_assoc_event_users[1]==1);
 assert(other.wr_iot_control_poisoned&&!other.wr_iot_control_users);
 assert(wr_ra2_direct_key_leave(&ad,&scope));
 setup(&ad,&event,2);assert(wr_ra2_direct_key_enter(&ad,&scope));
 ad.MacTab.Content[1].assoc_gen++;
 assert(!wr_ra2_direct_key_leave(&ad,&scope));
 assert(ad.wr_iot_control_poisoned&&ad.wr_iot_peer_table_owner.poisoned&&ad.wr_assoc_event_users[1]==1);
 puts("Direct key scope: retained peers, mutation exclusion, rollback and foreign/drift release PASS; native ioctl unbound");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-direct-key-scope-') as temp:
 d=Path(temp);(d/'check.c').write_text(unit)
 for flags in ([],['-DOS_ABL_FUNC_SUPPORT=1']):
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/'check.c'),'-o',str(d/'check')],check=True)
  subprocess.run([str(d/'check')],check=True)
