#!/usr/bin/env python3
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-status-endpoint-build-') as d:
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/'check-status-endpoint.c'),str(here/'status-endpoint.c'),str(here/'status-channel.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
