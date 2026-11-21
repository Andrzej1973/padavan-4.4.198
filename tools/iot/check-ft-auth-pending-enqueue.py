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
sys.argv=[str(here/'check-ft-pending-enqueue.py'),str(a.source)]
try:
    with contextlib.redirect_stdout(io.StringIO()):
        fixture=runpy.run_path(sys.argv[0])
finally:
    sys.argv=argv
module=runpy.run_path(str(here/'ft-auth-enqueue-composition.py'))
changed,prototype=module['compose_pending'](fixture['prepared']['common/mlme.c'])
start=changed.rindex('BOOLEAN wr_ft_auth_pending_enqueue_for_recv(')
body=changed[start:changed.index('\n}',start)+2]
addition='\n#ifdef DOT11R_FT_SUPPORT\n#include "ft-pending-queue.h"\n'+prototype+'\n'+body+'\n#endif\n'
assert changed.replace(addition,'',1)==fixture['prepared']['common/mlme.c']
assert 'wr_assoc_capture(' not in body
try:module['compose_pending'](changed)
except ValueError:pass
else:raise AssertionError('duplicate FT AUTH enqueue accepted')
prefix=fixture['prefix'].replace('#define ACTION_STATE_MACHINE 7',
 '#define ACTION_STATE_MACHINE 7\n#define AP_AUTH_STATE_MACHINE 8\n#define APMT2_PEER_AUTH_REQ 9')
prefix=prefix.replace('*machine=ACTION_STATE_MACHINE;*type=FT_CATEGORY_BSS_TRANSITION;',
 '*machine=AP_AUTH_STATE_MACHINE;*type=APMT2_PEER_AUTH_REQ;')
main=fixture['main'].replace('wr_ft_pending_enqueue_for_recv','wr_ft_auth_pending_enqueue_for_recv')
main=main.replace('action->Category=6;action->Action=1;action->StaMac[0]=42;action->TargetApAddr[0]=2;',
 'frame.Octet[0]=2;frame.Octet[2]=1;')
main=main.replace('SEND(sizeof(frame)-1,&frame)','SEND(LENGTH_802_11+5,&frame)')
main=main.replace('action->Action=3;', 'frame.Octet[2]=3;').replace('action->Action=1;', 'frame.Octet[2]=1;')
main=main.replace('elem->Machine==ACTION_STATE_MACHINE','elem->Machine==AP_AUTH_STATE_MACHINE')
with tempfile.TemporaryDirectory(prefix='ft-auth-enqueue-') as td:
    c=Path(td)/'check.c';exe=Path(td)/'check'
    c.write_text(prefix+prototype+'\n'+body+main)
    for flags in ([],['-DEAPOL_QUEUE_SUPPORT'],['-DCUSTOMER_DCC_FEATURE']):
        subprocess.run(['gcc','-std=gnu11','-O2','-fsanitize=address,undefined',
          '-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
        subprocess.run([str(exe)],check=True)
print('PASS | FT AUTH pending enqueue | single ticket move; failed enqueue retains owner; stale identity, queue limits, EAP/SNR variants; uninstalled')
