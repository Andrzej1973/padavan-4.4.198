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
    for name in ('record','down','pins','lifetime','wire','response','observe','terminal','ioctl','client','session','origin','rebind-wire','rebind-ioctl','rebind-client','rebind-controller'):
        binary=root/name
        subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
                        '-fsanitize=address,undefined','-fno-pie','-no-pie',
                        '-I'+str(here),str(here/(('check-physical-'+name+'.c') if name.startswith('rebind-') else ('check-physical-stop-'+name+'.c'))),
                        '-o',str(binary)]+(['-Wdeclaration-after-statement'] if name in ('response','rebind-wire','rebind-ioctl','rebind-client','rebind-controller') else [])+([str(here/'physical-stop-session.c')] if name=='session' else []),check=True)
        subprocess.run([str(binary)],check=True,timeout=15)
    for name in ('executor','retirement','candidate','terminal-composition','prior-close','main-binding','deferred-candidate','reset-binding','arm-admission','arm-publication','main-completion','cancel','terminal-replace','terminal-free','release','query','handler','dispatch','client-preparation','aux'):
        subprocess.run([sys.executable,'-B',str(here/('check-physical-stop-'+name+'.py'))],check=True,timeout=60)
for name in ('check-rc-physical-stop.py','check-rc-runtime.py','check-rc-quiesce.py','check-rc-physical-quiesce.py','check-physical-rebind-binding.py','check-physical-rebind-open-entry.py','check-physical-rebind-dispatch.py','check-rebind-start.py','check-rebind-network.py','check-rebind-rollback.py','check-rebind-commit.py','check-rebind-close.py','check-rebind-closed-rollback.py','check-rebind-runner.py','check-rebind-runner-close.py','check-rebind-active-stop.py','check-rc-rebind-owner.py','check-rc-rebind-reopen.py','check-rc-rebind-repeat.py'):
    subprocess.run([sys.executable,'-B',str(here/name)],check=True,timeout=60)
print('PASS physical-stop candidate host suite: uninstalled driver bindings, API transport and target/device acceptance remain pending')
