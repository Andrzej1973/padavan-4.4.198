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
unit=ns['prefix']+ns['actors']+'\n#include "ra2-direct-key-peer.h"\n'+setup+r'''
int main(void){
 RTMP_ADAPTER ad;MLME_QUEUE_ELEM event;struct wr_ra2_rekey_peer_scope scope;
 MAC_TABLE_ENTRY *entry=(void*)1;unsigned char absent[6]={77};
 setup(&ad,&event,2);expect_scoped=0;
 ad.MacTab.Content[2]=ad.MacTab.Content[1];ad.MacTab.Content[2].wcid=2;
 ad.MacTab.Content[2].func_tb_idx=1;ad.MacTab.Content[2].wdev=&ad.ApCfg.MBSSID[1].wdev;
 assert(wr_ra2_rekey_peers_enter(&ad,&scope));
 NdisAcquireSpinLock(&ad.MacTabLock);
 assert(wr_ra2_direct_key_peer_locked(&ad,&scope,ad.MacTab.Content[1].Addr,&entry)==1);
 assert(entry==&ad.MacTab.Content[1]);
 assert(wr_ra2_direct_key_peer_locked(&ad,&scope,absent,&entry)==0&&!entry);
 ad.MacTab.Content[1].assoc_gen++;
 assert(wr_ra2_direct_key_peer_locked(&ad,&scope,ad.MacTab.Content[1].Addr,&entry)==-1&&!entry);
 ad.MacTab.Content[1].assoc_gen--;
 ad.MacTab.Content[1].Addr[0]=7;
 assert(wr_ra2_direct_key_peer_locked(&ad,&scope,ad.MacTab.Content[2].Addr,&entry)==-1&&!entry);
 ad.MacTab.Content[1].Addr[0]=ad.MacTab.Content[2].Addr[0];
 ad.MacTab.Content[2].wdev=&ad.ApCfg.MBSSID[2].wdev;ad.MacTab.Content[2].func_tb_idx=2;
 scope.generations[2]=ad.MacTab.Content[2].assoc_gen;ad.wr_assoc_event_users[2]=1;
 assert(wr_ra2_direct_key_peer_locked(&ad,&scope,ad.MacTab.Content[1].Addr,&entry)==-1&&!entry);
 NdisReleaseSpinLock(&ad.MacTabLock);
 puts("Retained ra2 direct-key lookup: exact BSS, foreign/duplicate MAC and generation drift PASS; ioctl binding pending");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ra2-direct-key-peer-') as temp:
 d=Path(temp);(d/'check.c').write_text(unit)
 for flags in ([],['-DOS_ABL_FUNC_SUPPORT=1']):
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-function','-Wno-unused-parameter','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,'-I'+str(here),str(d/'check.c'),'-o',str(d/'check')],check=True)
  subprocess.run([str(d/'check')],check=True)
