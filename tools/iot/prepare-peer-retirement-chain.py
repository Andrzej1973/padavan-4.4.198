#!/usr/bin/env python3
"""Compose reviewed WDS/queue candidates; not production or lifetime acceptance."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path, help='full current recovery overlay before peer changes')
p.add_argument('output', type=Path, help='new scratch workspace; retain failed stages for inspection')
a = p.parse_args()
source = a.source.resolve(strict=True)
out = a.output.resolve()
if out.exists() or source == out or source in out.parents or out in source.parents:
    p.error('new separate scratch workspace required')
out.mkdir(parents=True)
here = Path(__file__).resolve().parent
steps = [
    ('wds', 'prepare-wds-recovery-reconciliation.py'),
    ('dequeue', 'prepare-wcid-dequeue-fence.py'),
    ('ps', 'prepare-wcid-ps-fence.py'),
    ('uapsd', 'prepare-wcid-uapsd-fence.py'),
    ('writer', 'prepare-wcid-reset-writer.py'),
    ('delete', 'prepare-uapsd-delete-join.py'),
    ('eosp', 'prepare-uapsd-eosp-release.py'),
    ('publication', 'prepare-tr-capability-publication.py'),
    ('bss-unlock', 'prepare-insertion-bss-unlock.py'),
    ('setup-result', 'prepare-tr-setup-result.py'),
    ('peer-ready', 'prepare-peer-ready-publication.py'),
    ('hardware-result', 'prepare-wcid-hardware-result.py'),
    ('hardware-delete', 'prepare-wcid-delete-result.py'),
    ('wds-retained', 'prepare-wds-detached-owner.py'),
    ('wds-peer-fence', 'prepare-wds-peer-fence.py'),
    ('wds-outer', 'prepare-wds-outer-operation.py'),
    ('wds-caller-refusal', 'prepare-wds-caller-refusal.py'),
    ('wds-caller-transaction', 'prepare-wds-caller-transaction.py'),
    ('wds-peer-delete', 'prepare-wds-peer-delete-gate.py'),
    ('wds-maintenance', 'prepare-wds-maintenance-refusal.py'),
    ('wds-slot-allocation', 'prepare-wds-slot-allocation-gate.py'),
    ('wds-retirement-close', 'prepare-wds-retirement-close-gate.py'),
    ('wds-delete-identity', 'prepare-wds-peer-delete-identity.py'),
    ('wds-ageout', 'prepare-wds-ageout-transaction.py'),
    ('wds-lock-lifetime', 'prepare-wds-lock-lifetime.py'),
    ('wds-ageout-identity', 'prepare-wds-ageout-identity-owner.py'),
    ('wds-hardware-consumer', 'prepare-wds-hardware-delete-consumer.py'),
    ('hardware-delete-busy', 'prepare-wcid-delete-busy-admission.py'),
    ('hardware-update-busy', 'prepare-wcid-update-busy-admission.py'),
    ('wds-delete-resume', 'prepare-wds-delete-resume.py'),
    ('wds-ageout-recovery', 'prepare-wds-ageout-recovery.py'),
    ('peer-hardware-insert', 'prepare-peer-hardware-insert-consumer.py'),
    ('peer-timer-fence', 'prepare-peer-timer-fence.py'),
    ('timer-task-owner', 'prepare-timer-task-owner.py'),
    ('timer-checked-join', 'prepare-timer-checked-join.py'),
    ('peer-failed-delete', 'prepare-peer-failed-delete-gates.py'),
    ('peer-reset-result', 'prepare-peer-reset-result.py'),
    ('ap-stop-result', 'prepare-ap-stop-result.py'),
    ('ap-shutdown-result', 'prepare-ap-shutdown-result.py'),
    ('legacy-close-result', 'prepare-legacy-close-result.py'),
    ('peer-table-owner', 'prepare-peer-table-owner.py'),
    ('peer-lock-lifetime', 'prepare-peer-lock-lifetime.py'),
    ('peer-open-transport', 'prepare-peer-open-transport.py'),
    ('peer-startup-insertion', 'prepare-peer-startup-insertion.py'),
    ('wds-startup-transaction', 'prepare-wds-startup-transaction.py'),
    ('wds-startup-loop', 'prepare-wds-startup-loop.py'),
    ('wds-configured-open', 'prepare-wds-configured-interface-open.py'),
    ('wds-table-transaction', 'prepare-wds-table-transaction.py'),
    ('main-open-table-claim', 'prepare-main-open-table-claim.py'),
    ('peer-close-table', 'prepare-peer-close-table.py'),
    ('peer-legacy-close', 'prepare-peer-legacy-close.py'),
    ('peer-close-executor', 'prepare-peer-close-executor.py'),
    ('peer-reset-executor', 'prepare-peer-reset-executor.py'),
    ('peer-wds-executor', 'prepare-peer-wds-executor.py'),
    ('peer-normal-insert', 'prepare-peer-normal-insert.py'),
    ('peer-delete-execution', 'prepare-peer-delete-execution.py'),
    ('adapter-free-result', 'prepare-adapter-free-result.py'),
    ('peer-adapter-release', 'prepare-peer-adapter-release.py'),
    ('pci-first-work-receipt', 'prepare-pci-first-work-receipt.py'),
    ('pci-child-snapshot', 'prepare-pci-child-snapshot.py'),
    ('netdev-ops-lifetime', 'prepare-netdev-ops-lifetime.py'),
    # Preserve the early tasklet join. Draft65 late-join ordering is excluded.
    ('nettask-exit-result', 'prepare-nettask-exit-result.py'),
    ('nettask-schedule', 'prepare-nettask-schedule.py'),
    ('nettask-release-fence', 'prepare-nettask-release-fence.py'),
    ('nettask-init-unwind', 'prepare-nettask-init-unwind.py'),
    ('aux-remove-close-guard', 'prepare-aux-remove-close-guard.py'),
    ('aux-family-close-result', 'prepare-aux-family-close-result.py'),
    ('aux-removing-close-admission', 'prepare-aux-removing-close-admission.py'),
    ('aux-family-close-owner', 'prepare-aux-family-close-owner.py'),
    ('aux-family-open-owner', 'prepare-aux-family-open-owner.py'),
    ('virtual-up-claim-only', 'prepare-virtual-up-claim-only.py'),
    ('virtual-down-owner-only', 'prepare-virtual-down-owner-only.py'),
    ('aux-family-close-retry', 'prepare-aux-family-close-retry.py'),
    ('aux-family-retry-scheduler', 'prepare-aux-family-retry-scheduler.py'),
]
current = source
receipts = []
for name, script in steps:
    target = out / name
    print('Preparing ' + name, flush=True)
    subprocess.run([sys.executable, str(here / script), str(current), str(target)], check=True)
    receipts.append({'stage': name, 'script': script,
                     'script_sha256': hashlib.sha256((here / script).read_bytes()).hexdigest()})
    current = target
manifest = {
    'source': str(source), 'candidate': str(current), 'stages': receipts,
    'files': {f.relative_to(current).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
              for f in sorted(current.rglob('*')) if f.is_file()},
    'scope': 'composed candidate only; reuse/completion identity and recovery remain open',
    'production_installed': False, 'target_compiled': False, 'runtime_verified': False,
}
(out / 'peer-chain.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
print('Composed candidate: ' + str(current), flush=True)
