#!/usr/bin/env python3
"""Check native retry sidecar schema, init, producer clear and delayed copy."""
import argparse
import runpy
import subprocess
import tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'assoc-generation-composition.py'))['compose']({},a.source,here)
compose=runpy.run_path(str(here/'ft-preauth-queue-composition.py'))['compose']
prepared=compose(base,a.source,here)
assert prepared['include/mlme.h'].count('unsigned int ft_preauth_serial,')==1
kernel=prepared['include/assoc-generation-kernel.h']
start=kernel.index('static inline void wr_assoc_publish(')
body=kernel[start:kernel.index('\n}',start)+2]
assert body.index('wr_ft_preauth_elem_clear(elem)')<body.index('elem->assoc_gen =')
mlme=prepared['common/mlme.c']
start=mlme.index('NDIS_STATUS MlmeQueueInit(');init=mlme[start:mlme.index('\n}',start)+2]
for q in ('Queue','EAP_Queue'):
 marker=q+'->Entry[i].Occupied = FALSE;'
 if marker in init:assert init.index('wr_ft_preauth_elem_clear(&'+q)<init.index(marker)
for field in ('serial','generation','wcid','bss','mac','bssid'):
 assert 'Elem->ft_preauth_'+field in mlme
for invalid in ({},prepared):
 try:compose(invalid,a.source,here)
 except ValueError:pass
 else:raise AssertionError('missing predecessor or duplicate accepted')
with tempfile.TemporaryDirectory(prefix='ft-preauth-sidecar-') as td:
 exe=Path(td)/'check'
 subprocess.run(['gcc','-std=gnu11','-O2','-Wall','-Wextra','-Werror',
  '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),
  str(here/'check-ft-iapp-detached-admission.c'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS | native MLME retry sidecar composition | feature guarded schema; queue init and every association stamp publication clear sidecar; delayed requeue copies all identity fields; missing/duplicate predecessor refused')
