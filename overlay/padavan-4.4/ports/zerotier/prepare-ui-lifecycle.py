#!/usr/bin/env python3
"""Integrate ZeroTier WebUI, monitor and policy after base lifecycle hardening."""
import argparse
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source.resolve()
here = Path(__file__).resolve().parent
for helper in (
    'prepare-managed-network.py', 'prepare-status-page.py',
    'prepare-action-lock.py', 'prepare-monitor-lifecycle.py',
    'prepare-policy-lifecycle.py', 'prepare-firewall-hook.py',
    'prepare-service-dispatch.py',
    'prepare-storage-persistence.py', 'prepare-persistence-events.py',
):
    subprocess.run([sys.executable, str(here / helper), str(root)], check=True)
print('ZeroTier WebUI, lifecycle, monitor and firewall integrated; runtime verification pending')
