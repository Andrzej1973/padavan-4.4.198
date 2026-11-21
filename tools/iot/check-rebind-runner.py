#!/usr/bin/env python3
"""Exercise actual rebind runner with failure-injected component adapters."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-rebind-runner-') as d:
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/'check-rebind-runner.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
