#!/usr/bin/env python3
"""Compile and run actual interprocess status transport with sanitizers."""
from pathlib import Path
import subprocess,tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='iot-status-transport-build-') as d:
 binary=Path(d)/'check'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(here/'check-status-channel.c'),str(here/'status-channel.c'),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True)
