#!/usr/bin/env python3
"""Regress the CLOSE probe sibling-call size false positive with the real wrapper."""
from pathlib import Path
import re
import runpy
import subprocess
import tempfile

here = Path(__file__).resolve().parent
source = runpy.run_path(str(here / 'check-close-bindings-target-tu.py'))['probe_source'](Path('/driver'), here)
match = re.search(r'int wr_iot_close_bindings_target_probe\([^}]+\n}', source)
assert match
wrapper = match.group()
prefix = '''typedef struct {int value;} RTMP_ADAPTER;
typedef void *PNET_DEV;
struct ifreq {int value;};
'''
implementations = {
    'body': '''static __attribute__((noinline,noipa)) int wr_iot_driver_close_reply(
RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq,unsigned char *wire){
return ad->value + rq->value + wire[0] + (dev!=0);
}
''',
    'refusal': '''static int wr_iot_driver_close_reply(
RTMP_ADAPTER *ad,PNET_DEV dev,struct ifreq *rq,unsigned char *wire){
(void)ad;(void)dev;(void)rq;(void)wire;return -16;
}
''',
}
implementations['body-sibling'] = implementations['body']
sizes = {}
with tempfile.TemporaryDirectory(prefix='wr-close-probe-codegen-') as scratch:
    root = Path(scratch)
    for case, implementation in implementations.items():
        c = root / (case + '.c')
        obj = root / (case + '.o')
        selected = wrapper
        if case == 'body-sibling':
            selected = selected.replace(' asm volatile("" : : "r" (status));', '')
        c.write_text(prefix + implementation + selected)
        # Host CET entry prefixes add four bytes unrelated to the MIPS gate.
        subprocess.run(['gcc', '-O2', '-fcf-protection=none', '-Wall', '-Wextra', '-Werror', '-c', str(c), '-o', str(obj)], check=True)
        symbols = subprocess.check_output(['nm', '-S', str(obj)], text=True)
        row = next(line.split() for line in symbols.splitlines()
                   if line.endswith(' wr_iot_close_bindings_target_probe'))
        size = int(row[1], 16)
        sizes[case] = size
        assert (size > 8) == (case == 'body'), (case, row)
print('Host probe bytes', sizes)
print('PASS actual CLOSE probe wrapper retains a nontrivial call while constant refusal still fails the unchanged size gate; host code generation only')
