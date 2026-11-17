#!/usr/bin/env python3
"""Compile producer's literal reservation/field fragments via ABI extractor.

This checks generated C, not a full SDK translation unit or target firmware.
"""
from pathlib import Path
import ast
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
tree=ast.parse((here/'prepare-rc.py').read_text())
def literal(name):
 matches=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in n.targets) and isinstance(n.value,(ast.Constant,ast.List))]
 if len(matches)!=1:raise ValueError('Producer literal changed: '+name)
 return matches[0]
include=literal('include');cold=literal('cold').replace(r'\t','\t')
fields='\n'.join(new for _,new in literal('replacements'))
with tempfile.TemporaryDirectory(prefix='wr-generation-profile-stage-') as directory:
 root=Path(directory);source=root/'source/trunk/user/rc/ralink.c';source.parent.mkdir(parents=True)
 selector=root/'selector'
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/'check-generation-profile-selector.c'),'-o',str(selector)],check=True)
 subprocess.run([str(selector)],check=True,timeout=15)

 source.write_text(include+cold+'\n#endif\n'+fields)
 generated=root/'check.c'
 subprocess.run([sys.executable,'-B',str(here/'prepare-profile-check.py'),str(root/'source'),str(generated)],check=True)
 for mode in ('original','coordinated'):
  binary=root/mode
  command=['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-DBOARD_WR1200JS']
  if mode=='coordinated':command+=['-DUSE_WR_BAND_STEERING_PROFILE']
  subprocess.run(command+[str(generated),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=15)
print('PASS literal producer cold admission and field staging via actual ABI extractor, original/coordinated host modes; full SDK/MIPS evidence still required')
