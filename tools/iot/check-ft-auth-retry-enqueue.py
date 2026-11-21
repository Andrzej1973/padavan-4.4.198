#!/usr/bin/env python3
"""Execute generated native AUTH retry enqueue in default/EAP/SNR forms."""
import argparse,contextlib,io,runpy,subprocess,sys,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
argv=sys.argv[:];sys.argv=[str(here/'check-ft-auth-enqueue.py'),str(a.source)]
try:
 with contextlib.redirect_stdout(io.StringIO()):data=runpy.run_path(sys.argv[0])
finally:sys.argv=argv
module=runpy.run_path(str(here/'ft-auth-enqueue-composition.py'))
changed,prototype=module['compose_retry'](data['fixture']['prepared'])
start=changed.rindex('BOOLEAN wr_ft_auth_retry_enqueue_for_recv(')
body=changed[start:changed.index('\n}',start)+2]
assert 'wr_assoc_capture(' not in body
try:module['compose_retry'](changed)
except ValueError:pass
else:raise AssertionError('duplicate retry preparation accepted')
prefix=data['prefix'].replace('typedef struct {unsigned assoc_gen;',
 'typedef struct {unsigned ft_preauth_serial,ft_preauth_generation,ft_preauth_wcid,ft_preauth_bss;unsigned char ft_preauth_mac[6],ft_preauth_bssid[6];unsigned assoc_gen;',1)
prefix+='\n#include "ft-preauth-queue.h"\n'
main=data['main'].replace('wr_ft_auth_mlme_enqueue_for_recv','wr_ft_auth_retry_enqueue_for_recv')
main=main.replace('struct wr_ft_peer_stamp expected={0};assert(wr_ft_peer_capture_locked(&ad,7,2,e->Addr,&expected));',
 'struct wr_ft_preauth_identity expected={.serial=19,.generation=1,.wcid=7,.bss=2,.mac={42},.bssid={2}};')
main=main.replace('expected.addr','expected.mac').replace('struct wr_ft_peer_stamp invalid','struct wr_ft_preauth_identity invalid')
main=main.replace('assert(!wr_ft_peer_current_locked(&ad,&expected));',
 '''assert(queued->ft_preauth_serial==19&&queued->ft_preauth_generation==1);
 assert(queued->ft_preauth_wcid==7&&queued->ft_preauth_bss==2);
 assert(!memcmp(queued->ft_preauth_mac,expected.mac,6)&&!memcmp(queued->ft_preauth_bssid,expected.bssid,6));
 struct wr_ft_preauth_identity snapshot={0};
 assert(wr_ft_preauth_elem_snapshot(queued,&snapshot));
 assert(snapshot.serial==19&&snapshot.generation==1);''')
main=main.replace('assert(wr_ft_peer_capture_locked(&ad,7,2,e->Addr,&expected));',
 'expected.serial=20;expected.generation=2;')
main=main.replace('assert(ad.Mlme.Queue.Entry[1].assoc_gen==2);',
 'assert(ad.Mlme.Queue.Entry[1].assoc_gen==2&&ad.Mlme.Queue.Entry[1].ft_preauth_serial==20);')
needle=' assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),NULL,&expected));'
main=main.replace(needle,''' expected.serial=0;
 assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));expected.serial=19;
 expected.bssid[0]=9;
 assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));expected.bssid[0]=2;
'''+needle)
with tempfile.TemporaryDirectory(prefix='ft-auth-retry-enqueue-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(prefix+prototype+'\n'+body+main)
 for flags in ([],['-DEAPOL_QUEUE_SUPPORT'],['-DCUSTOMER_DCC_FEATURE']):
  subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
print('PASS | native AUTH retry enqueue | immutable captured serial/generation across slot reuse; full retry sidecar; null/short/AUTH/BSS/WCID/serial/BSSID refusals; queue limits; default/EAP/SNR')
