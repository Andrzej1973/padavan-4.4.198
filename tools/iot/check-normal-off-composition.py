#!/usr/bin/env python3
"""Run actual snapshot/service/controller composition before target builds."""
from pathlib import Path
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-normal-off-') as d:
    root=Path(d)
    subprocess.run([sys.executable,str(here/'prepare-request-stage-check.py'),d],check=True)
    binary=root/'check'
    units=('check-request-snapshot.c','request-stage.c','request-snapshot.c',
           'disable-services.c','disable-controller.c','profile.c')
    subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie',
                    '-I'+d,'-I'+str(here),*[str(here/n) for n in units],
                    '-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True)
