#!/usr/bin/env python3
"""Stage close-only PCI preclose inside bounded recovery drain; isolated only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();src=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or src==out or src in out.parents or out in src.parents:p.error('new separate output required')
parent=json.loads(src.with_name(src.name+'.manifest.json').read_text())
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if actual!=parent['merged_driver_sha256'] or parent.get('production_installed') is not False:p.error('changed merged input')
name='os/linux/pci_main_dev.c';raw=(src/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='a9abed6d4dbaadf88503d2cde5d0183ccadb2b0e42ff53bb4e3722f211d51b4d':p.error('unreviewed PCI source')
s=raw.decode();replacements=[
 ('#define WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS 3U','#include "wr-iot-pci-netdev-preclose.inc"\n#define WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS (WDEV_NUM_MAX + 4U)'),
 (' int next_pending, completed;',' int next_pending, completed, preclosed;'),
 (' for (round = 0; round <= WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS; round++) {',' for (round = 0; round <= WR_IOT_PCI_RECOVERY_DRAIN_ROUNDS; round++) {\n  preclosed = wr_iot_pci_netdev_preclose(adapter, adapter->net_dev) == NDIS_STATUS_SUCCESS;'),
 ('  if (decision == WR_PCI_DRAIN_COMPLETE)\n   completed =','  if (decision == WR_PCI_DRAIN_COMPLETE && preclosed)\n   completed ='),
 ('  if (decision == WR_PCI_DRAIN_COMPLETE) return completed;','  if (decision == WR_PCI_DRAIN_COMPLETE && preclosed) return completed;\n  /* A joined close may now be terminal; recheck before advancing the owner. */')]
# Physical close can still need the command worker. Terminalize it only
# after all preclose tickets and their recovery owners have been drained.
block_start=s.index('#if defined(MT7603) && defined(DMA_RESET_SUPPORT)',s.index('static VOID DEVEXIT rt_pci_remove('))
block_end=s.index('#endif\n',block_start)+len('#endif\n')
terminal=s[block_start:block_end]
assert 'wr_iot_terminal_command_join_checked(adapter)' in terminal
stop_anchor='\t\tRTMP_IRQ_LOCK(&adapter->wr_iot_transition_lock, flags);\n\t\twr_iot_main_recovery_request_stop(&adapter->wr_iot_main_recovery);'
assert s.count(stop_anchor)==1
replacements.extend([(terminal,''),(stop_anchor,terminal+stop_anchor)])
changed=s
undo=[]
for old,new in replacements:
 if changed.count(old)!=1:p.error('PCI anchor mismatch: '+old)
 position=changed.index(old);undo.append((position,old,new))
 changed=changed.replace(old,new)
restored=changed
for position,old,new in reversed(undo):
 assert restored[position:position+len(new)]==new
 restored=restored[:position]+old+restored[position+len(new):]
assert restored==s
shutil.copytree(src,out);(out/name).write_text(changed)
helper='include/wr-iot-pci-netdev-preclose.inc'
assert not (out/helper).exists()
shutil.copyfile(Path(__file__).with_name('pci-netdev-preclose.inc'),out/helper)
for rel in (name,helper):
 digest=hashlib.sha256((out/rel).read_bytes()).hexdigest()
 parent['merged_driver_sha256'][rel]=digest;parent['candidate_driver_sha256'][rel]=digest
parent.update(production_installed=False,target_compiled=False,runtime_verified=False)
parent['pci_netdev_preclose_layer']={'target_compiled':False,'runtime_verified':False,'callback_retirement_proven':False}
out.with_name(out.name+'.manifest.json').write_text(json.dumps(parent,indent=2)+'\n')
print('Staged bounded child/main preclose before recovery stop; release remains fail-closed')
