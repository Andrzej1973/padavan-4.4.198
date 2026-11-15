"""Compile actual DOWN fragments in their generated driver include order."""
from pathlib import Path
import runpy,subprocess,tempfile
here=Path(__file__).resolve().parent
base=runpy.run_path(str(here/'release-dispatch-composition.py'))['compose']
compose=runpy.run_path(str(here/'down-dispatch-composition.py'))['compose']
entry=base((here/'driver-api-closed-entry.inc').read_text())
generated=compose(entry)
binding='#include "precreated-down-binding.inc"'
reply='#include "precreated-down-reply.inc"'
assert generated.index(binding)<generated.index(reply)
for changed in [entry.replace(binding,''),entry.replace(binding,binding+'\n'+binding)]:
 try:compose(changed)
 except ValueError:pass
 else:raise AssertionError('missing/duplicate binding accepted')
ordered=[line for line in generated.splitlines() if line in (binding,reply)]
source=(here/'check-precreated-down-binding.c').read_text()
assert source.count(binding)==1
source=source.replace(binding,'\n'.join(ordered))
with tempfile.TemporaryDirectory(prefix='wr-down-driver-order-') as d:
 p=Path(d)/'check.c';p.write_text(source);binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu89','-Wall','-Wextra','-Werror',
                 '-Wno-declaration-after-statement','-O2','-fsanitize=address,undefined',
                 '-fno-pie','-no-pie','-I'+str(here),str(p),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=20)
 # Reproduce the exact old failure by reversing only those includes.
 p.write_text(source.replace('\n'.join(ordered),'\n'.join(reversed(ordered))))
 bad=subprocess.run(['gcc','-std=gnu89','-Werror=implicit-function-declaration',
                     '-I'+str(here),'-c',str(p),'-o',str(Path(d)/'bad.o')],
                    text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 assert bad.returncode and "static declaration" in bad.stderr
 assert 'wr_iot_precreated_down_observed' in bad.stderr
print('PASS generated driver DOWN include order: actual binding/reply compile GNU89 Werror/sanitizers, old order reproduces static-after-implicit error, missing/duplicate binding refuses; no MIPS/device claim')
