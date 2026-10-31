#!/usr/bin/env python3
"""Run bounded host checks for the isolated v25b successor; no device IO."""
import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
candidate, output = a.candidate.resolve(), a.output.resolve()
if output.exists() or candidate == output or candidate in output.parents or output in candidate.parents:
    p.error('Output must be new and separate')
receipt = json.loads(candidate.with_name(candidate.name+'-generation.json').read_text())
actual = {f.relative_to(candidate).as_posix(): hashlib.sha256(f.read_bytes()).hexdigest()
          for f in candidate.rglob('*') if f.is_file()}
if actual != receipt['candidate_sha256']:
    p.error('Candidate differs from preparation receipt')
output.mkdir(parents=True)
here = Path(__file__).resolve().parent
checks = []
def run(name, command):
    result = subprocess.run(list(map(str, command)), capture_output=True, text=True, timeout=30)
    (output/(name+'.txt')).write_text(result.stdout+result.stderr)
    if result.returncode:
        raise SystemExit(f'{name} failed ({result.returncode}); see {output}')
    checks.append(name)
run('caller-coverage', [sys.executable, here/'check-virtual-if-call-coverage.py', candidate])
run('extract-ledger', [sys.executable, here/'prepare-beacon-txs-ledger-check.py', candidate,
                     output/'ledger.c', '--expect-generation-exhaustion'])
run('extract-close', [sys.executable, here/'prepare-checked-close-check.py', candidate,
                    output/'close.c'])
for name, source, flags in (
    ('ledger', output/'ledger.c', []),
    ('close', output/'close.c', []),
    ('post-open', here/'check-mbss-post-open.c', ['-DWR_IOT_V40'])):
    binary = output/(name+'.exe')
    run(name+'-compile', ['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2',
                         *flags, '-I'+str(candidate/'include'), source, '-o', binary])
    run(name, [binary])
(output/'result.json').write_text(json.dumps({'host_checks': checks,
    'candidate_sha256': actual, 'target_compiled': False,
    'production_installed': False, 'runtime_verified': False}, indent=2)+'\n')
print('PASS successor host checks; target and hardware acceptance remain open')
