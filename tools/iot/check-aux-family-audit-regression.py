#!/usr/bin/env python3
"""Ensure the remove-order audit accepts STALLED joins but rejects missing normal joins."""
import argparse
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='wr-aux-order-regression-') as t:
 root=Path(t)
 subprocess.run([sys.executable,str(here/'audit-aux-family-retry-scheduler.py'),str(a.candidate),str(root/'positive.json')],check=True)
 mutant=root/'candidate';shutil.copytree(a.candidate,mutant)
 path=mutant/'os/linux/pci_main_dev.c';s=path.read_text()
 start=s.index('static VOID DEVEXIT rt_pci_remove(')
 stop=s.index('if (!wr_iot_pci_retirement_stop_requested(',start)
 join=s.index('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);',stop)
 s=s[:join]+s[join:].replace('cancel_work_sync(&adapter->wr_iot_aux_family_retry_work);','/* regression: normal join missing */',1)
 path.write_text(s)
 result=subprocess.run([sys.executable,str(here/'audit-aux-family-retry-scheduler.py'),str(mutant),str(root/'negative.json')],capture_output=True,text=True)
 if result.returncode==0 or 'AssertionError' not in result.stderr:
  raise SystemExit('Missing normal join was not rejected by the audit invariant')
print('PASS ABI610 regression: STALLED plus normal joins accepted; missing normal join rejected')
