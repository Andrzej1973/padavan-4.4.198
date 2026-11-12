#!/usr/bin/env python3
"""Run existing standalone host fixtures before the expensive optional build.

The WDS preflight compiles the producer's literal capture. The full candidate
pipeline must still check that capture in its actual prepared driver source.
"""
import ast
from pathlib import Path
import re
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
text = (here / 'ci-compile-merged-candidate.sh').read_text()
loops = re.findall(r'^  for fixture in (check-mcu-sender-owner [^\n]+); do$', text, re.M)
if len(loops) != 1:
    raise RuntimeError('Standalone host fixture list changed')
names = loops[0].split()
if len(names) != len(set(names)) or not all(re.fullmatch(r'check-[a-z0-9-]+', n) for n in names):
    raise RuntimeError('Invalid standalone fixture names')
producer = ast.parse((here / 'prepare-wds-unregister-generation.py').read_text())
captures = [ast.literal_eval(node.value) for node in producer.body
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'capture' for t in node.targets)]
if len(captures) != 1 or not isinstance(captures[0], str):
    raise RuntimeError('WDS producer capture changed')
with tempfile.TemporaryDirectory(prefix='wr-iot-host-preflight-') as scratch:
    root = Path(scratch)
    for name in names:
        binary = root / name
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                        '-I'+str(here), str(here / (name+'.c')), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True)
    subprocess.run([sys.executable, '-B', str(here / 'check-close-owner-composition.py')], check=True)
    subprocess.run([sys.executable, '-B', str(here / 'check-close-dispatch-composition.py')], check=True)
    subprocess.run([sys.executable, '-B', str(here / 'check-close-probe-codegen.py')], check=True)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I'+str(here), str(here / 'check-driver-close-controller.c'),
                    '-o', str(root / 'check-driver-close-controller')], check=True)
    subprocess.run([str(root / 'check-driver-close-controller')], check=True)
    candidate = root / 'wds-producer-capture'
    (candidate / 'ap').mkdir(parents=True)
    (candidate / 'ap/ap_wds.c').write_text(captures[0]+'\t\t\tRtmpOSNetDevDetach(wdev->if_dev);\nwr_generation, 1);\n')
    subprocess.run([sys.executable, '-B', str(here / 'check-wds-unregister-generation.py'), str(candidate)], check=True)
print('PASS early host compatibility:', len(names), 'existing standalone fixtures, CLOSE composition and WDS producer capture; actual driver binding checked later')
