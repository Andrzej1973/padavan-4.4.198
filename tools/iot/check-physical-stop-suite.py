#!/usr/bin/env python3
"""Reproduce all physical-stop candidate checks without installing driver code.

These are host source/composition checks, not firmware or device acceptance.
"""
from pathlib import Path
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-physical-stop-suite-') as d:
    root=Path(d)
    for name in ('record','down','pins','lifetime','wire','response','observe','terminal','ioctl'):
        binary=root/name
        subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
                        '-fsanitize=address,undefined','-fno-pie','-no-pie',
                        '-I'+str(here),str(here/('check-physical-stop-'+name+'.c')),
                        '-o',str(binary)],check=True)
        subprocess.run([str(binary)],check=True,timeout=15)
    for name in ('executor','retirement','candidate','terminal-composition','prior-close','main-binding','deferred-candidate','reset-binding','arm-admission','arm-publication'):
        subprocess.run([sys.executable,'-B',str(here/('check-physical-stop-'+name+'.py'))],check=True,timeout=60)
print('PASS physical-stop candidate host suite: uninstalled driver bindings, API transport and target/device acceptance remain pending')
