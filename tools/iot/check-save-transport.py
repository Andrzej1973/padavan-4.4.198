#!/usr/bin/env python3
"""Actual codec and real filesystem mailbox compatibility checks."""
from pathlib import Path
import subprocess
import tempfile
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-save-transport-') as directory:
 for name in ('check-control-record','check-config-mailbox','check-save-mailbox'):
  binary=Path(directory)/name
  source=[here/(name+'.c')]+([] if name=='check-control-record' else [here/'control-mailbox.c'])
  subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
                  '-I'+str(here),*map(str,source),'-o',str(binary)],check=True)
  subprocess.run([str(binary)],check=True,timeout=15)

with tempfile.TemporaryDirectory(prefix='wr-save-unbound-') as directory:
 binary=Path(directory)/'check';queue=Path(directory)/'queue'
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',
 '-DWR_IOT_CONTROL_DIRECTORY="'+str(queue)+'"','-DWR_IOT_NOTIFY()=((void)0)','-I'+str(here),
 *[str(here/name) for name in ('check-save-unbound.c','control-server.c','control-client.c','control-mailbox.c')],'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
