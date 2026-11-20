#!/usr/bin/env python3
"""Execute prepared exact-stamp FT AUTH enqueue with native-body host actors."""
import argparse
import contextlib
import io
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
here=Path(__file__).resolve().parent
argv=sys.argv[:]
sys.argv=[str(here/'check-ft-enqueue-generation.py'),str(a.source)]
try:
    with contextlib.redirect_stdout(io.StringIO()):
        fixture=runpy.run_path(sys.argv[0])
finally:
    sys.argv=argv
module=runpy.run_path(str(here/'ft-auth-enqueue-composition.py'))
changed,prototype=module['compose'](fixture['prepared'])
start=changed.rindex('BOOLEAN wr_ft_auth_mlme_enqueue_for_recv(')
body=changed[start:changed.index('\n}',start)+2]
addition='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-peer-generation.h"\n'+prototype+'\n'+body+'\n#endif\n'
assert changed.replace(addition,'',1)==fixture['prepared']
assert 'wr_assoc_capture(' not in body
try:module['compose'](changed)
except ValueError:pass
else:raise AssertionError('duplicate FT AUTH enqueue accepted')
prefix=fixture['prefix'].replace('#define ACTION_STATE_MACHINE 7',
 '#define ACTION_STATE_MACHINE 7\n#define AP_AUTH_STATE_MACHINE 8\n#define APMT2_PEER_AUTH_REQ 9')
prefix=prefix.replace('*machine=ACTION_STATE_MACHINE;*type=FT_CATEGORY_BSS_TRANSITION;',
 '*machine=AP_AUTH_STATE_MACHINE;*type=APMT2_PEER_AUTH_REQ;')
main=fixture['main'].replace('wr_ft_mlme_enqueue_for_recv','wr_ft_auth_mlme_enqueue_for_recv')
main=main.replace('frame.Hdr.Addr2[0]=42;',
 'frame.Hdr.Addr2[0]=42;frame.Octet[0]=2;frame.Octet[2]=1;',1)
main=main.replace('queued->Machine==ACTION_STATE_MACHINE&&queued->MsgType==6',
 'queued->Machine==AP_AUTH_STATE_MACHINE&&queued->MsgType==APMT2_PEER_AUTH_REQ')
needle=' assert(ad.Mlme.Queue.Num==1);'
extra=''' assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),NULL,&expected));
 for(unsigned i=0;i<6;i++){
  frame.Octet[i]^=1;
  assert(!ENQUEUE(&ad,7,&rssi,sizeof(frame),&frame,&expected));
  frame.Octet[i]^=1;
 }
'''+needle
assert main.count(needle)==1
main=main.replace(needle,extra)
with tempfile.TemporaryDirectory(prefix='ft-auth-enqueue-') as td:
    c=Path(td)/'check.c';exe=Path(td)/'check'
    c.write_text(prefix+prototype+'\n'+body+main)
    for flags in ([],['-DEAPOL_QUEUE_SUPPORT'],['-DCUSTOMER_DCC_FEATURE']):
        subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined',
          '-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('PASS | FT AUTH native enqueue | exact stamp across slot reuse; null/short/wrong AUTH and BSS/WCID refusal; queue limits; EAP/SNR variants; uninstalled')
