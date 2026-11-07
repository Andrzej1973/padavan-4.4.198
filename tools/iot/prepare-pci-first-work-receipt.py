#!/usr/bin/env python3
"""Record first PCI work join only after actual synchronous cancellations."""
import argparse,hashlib,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
rel='os/linux/pci_main_dev.c';f=src/rel
if hashlib.sha256(f.read_bytes()).hexdigest()!='5580a0b7464be7e1476489932020b031595396a1e7addba808616d709dbab047':p.error('unreviewed PCI source')
s=f.read_text();sig='static VOID DEVEXIT rt_pci_remove(';start=s.index(sig);end=s.index('\n}',start)+2
body=s[start:end]
old='\t\twr_iot_pci_retirement_stop_requested(&adapter->wr_iot_pci_retirement, 1);'
if body.count(old)!=1:p.error('changed stop request')
body=body.replace(old,'''\t\tif (!wr_iot_pci_retirement_stop_requested(&adapter->wr_iot_pci_retirement, 1)) {
\t\t\tRTMP_IRQ_UNLOCK(&adapter->wr_iot_transition_lock, flags);
\t\t\treturn;
\t\t}''',1)
old='\t\tif (adapter->wr_iot_main_recovery.deferred_owners) {'
if body.count(old)!=2:p.error('changed work-join guards')
body=body.replace(old,'''\t\tif (adapter->wr_iot_main_recovery.deferred_owners ||
\t\t    !adapter->wr_iot_main_recovery.stop_requested ||
\t\t    !wr_iot_pci_retirement_work_joined(&adapter->wr_iot_pci_retirement, 1)) {''',1)
shutil.copytree(src,out);(out/rel).write_text(s[:start]+body+s[end:],encoding='utf-8',newline='\n')
print('Staged first work-join receipt after actual cancellation; child/root/final release still open')
