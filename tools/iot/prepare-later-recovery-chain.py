#!/usr/bin/env python3
"""Replay isolated ownership/recovery stages to corrected v25b; never install or contact a device."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path, help='Reviewed composition for the selected input stage')
p.add_argument('output', type=Path, help='New separate workspace')
p.add_argument('--prior-manifest', required=True, type=Path)
p.add_argument('--input-stage', choices=['main-open', 'v7', 'v11', 'v14', 'v19'], default='v19')
p.add_argument('--source-tree', type=Path, help='Pinned mt76x3 headers required for v7 input')
a = p.parse_args()
source = a.source.resolve(strict=True)
output = a.output.resolve()
manifest = a.prior_manifest.resolve(strict=True)
if output.exists() or source in output.parents or output in source.parents:
    p.error('output must be new and separate from input')
base = json.loads(manifest.read_text(encoding='utf-8'))
rows = base['files']
expected = {r['path']: r['sha256'] for r in rows}
def hashes(tree):
    return {f.relative_to(tree).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
            for f in tree.rglob('*') if f.is_file()}
if (base.get('production_installed') is not False or
        base.get({'main-open':'main_open_claim_composed', 'v7':'main_recovery_work_initialized', 'v11':'aux_remove_results_staged', 'v14':'mbss_open_claim_composed',
                  'v19':'mbss_steering_race_staged'}[a.input_stage]) is not True or
        len(expected) != len(rows) or hashes(source) != expected):
    p.error('expected intact nonproduction '+a.input_stage+' input and manifest')
if a.input_stage in ('main-open', 'v7', 'v11') and manifest != source.with_name(source.name+'-composition.json'):
    p.error('early composers require the canonical sibling manifest')
if a.input_stage in ('main-open', 'v7') and (not a.source_tree or not a.source_tree.is_dir()):
    p.error('v7 requires --source-tree with pinned donor headers')
output.mkdir(parents=True)
here = Path(__file__).resolve().parent
records = []
def run(script, *args):
    command = [sys.executable, str(here / script), *map(str, args)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    (output / (str(len(records))+'-'+script+'.log')).write_text(
        result.stdout+result.stderr, encoding='utf-8')
    records.append({'script': script, 'sha256': hashlib.sha256((here/script).read_bytes()).hexdigest(),
                    'returncode': result.returncode})
    if result.returncode:
        raise SystemExit('Preparation failed: '+script+'; preserved logs in '+str(output))
previous = source
if a.input_stage == 'main-open':
    run('prepare-composed-mt7603-radio-off.py', previous, output/'radio-off')
    run('prepare-composed-main-close.py', output/'radio-off', output/'v6')
    run('prepare-main-recovery-work-candidate.py', output/'v6', output/'v7')
    previous = output/'v7'
if a.input_stage in ('main-open', 'v7'):
    for label, script in (
        ('v8', 'prepare-pci-remove-detach-guard.py'),
        ('v9', 'prepare-pci-remove-work-joins.py'),
        ('v10', 'prepare-pci-transaction-observation.py')):
        destination = output / label
        run(script, previous, destination)
        previous = destination
    run('prepare-remove-result-composition.py', previous, output/'v11',
        '--source-tree', a.source_tree.resolve(strict=True))
    previous = output/'v11'
if a.input_stage in ('main-open', 'v7', 'v11'):
    run('prepare-mbss-checked-stop-candidate.py', previous, output/'v12')
    run('prepare-mbss-open-claim-composition.py', previous, output/'v12', output/'v14')
    previous = output/'v14'
if a.input_stage in ('main-open', 'v7', 'v11', 'v14'):
    for label, script in (
        ('v15b', 'prepare-mbss-steering-ready-candidate.py'),
        ('v16b', 'prepare-mbss-steering-down-candidate.py'),
        ('v17', 'prepare-mbss-open-wakeup-candidate.py'),
        ('v18', 'prepare-reset-ticket-wakeup-candidate.py'),
        ('v19', 'prepare-mbss-steering-race-candidate.py')):
        destination = output / label
        run(script, previous, destination)
        previous = destination
    manifest = output / 'v19-composition.json'
for label, script in (
    ('v20', 'prepare-main-readiness-verify-candidate.py'),
    ('v21', 'prepare-main-verify-rollback-candidate.py'),
    ('v22', 'prepare-main-recovery-rtnl-candidate.py'),
    ('v23b', 'prepare-main-recovery-reaper-candidate.py'),
    ('v24c', 'prepare-pci-recovery-drain-candidate.py'),
    ('v25b', 'prepare-beacon-producer-candidate.py'),
    ('corrected', 'prepare-v25b-generation-bound.py')):
    destination = output / label
    extra = ['--prior-manifest', manifest] if label == 'v21' else []
    run(script, previous, destination, *extra)
    if label == 'v24c':
        run('check-pci-recovery-drain-candidate.py', destination)
    previous = destination
(output/'chain.json').write_text(json.dumps({
    'source':str(source), 'input_sha256':expected, 'steps':records,
    'candidate_sha256':hashes(previous), 'target_compiled':False,
    'production_installed':False, 'runtime_verified':False,
    'scope':a.input_stage+' onward only; upstream preparation not established'
}, indent=2)+'\n', encoding='utf-8')
print('PASS isolated later-chain preparation; no target or device acceptance')
