#!/usr/bin/env python3
"""Preserve v25b later stages with generation and readiness corrections."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
source, output = a.source.resolve(), a.output.resolve()
if output.exists() or source == output or source in output.parents or output in source.parents:
    p.error('Output must be new and separate')
files = {f.relative_to(source): f.read_bytes() for f in source.rglob('*') if f.is_file()}
name = Path('tx_rx/txs.c')
original = files[name]
digest = lambda b: hashlib.sha256(b).hexdigest()
payloads = dict(files)
if digest(original) != 'db696253451cae6754f02532cfeb00999829e6d2e2d985b80c424112836ff2f5':
    if digest(original) != 'ea48b9e6ca6d4b327a0d2cc8e0bc1f6b774e4e6f990180d174bdbcb62b484520':
        p.error('Unreviewed v25b TxS source')
    newline = '\r\n' if b'\r\n' in original else '\n'
    s = original.decode('utf-8').replace('\r\n', '\n')
    anchor = '\tfor (scan = 0; scan < TXS_STATUS_NUM; scan++) {'
    wrap = '\tif (!TxSCtl->ReservationGeneration)\n\t\tTxSCtl->ReservationGeneration++;\n'
    if s.count(anchor) != 1 or s.count(wrap) != 1:
        p.error('Changed v25b allocator anchors')
    s = s.replace(anchor, '''\tif (TxSCtl->ReservationGeneration == (UINT32)~0U) {
\t\tRTMP_SPIN_UNLOCK_IRQRESTORE(&TxSCtl->TxSStatusLock, &Flags);
\t\treturn -1;
\t}
''' + anchor, 1).replace(wrap, '', 1)
    payloads[name] = s.replace('\n', newline).encode('utf-8')
ready_name = Path('include/virtual-open-claim.h')
if digest(files[ready_name]) != '8bb2017fae17f18ef6d31e50dc577aeb9db83497b049d246b36b29b1677a913b':
    if digest(files[ready_name]) != 'bbe354c2fbeb6e1a0db027f1782475a16eb6cdf1d6dd62165470bb0f3e711bda':
        p.error('Unreviewed v25b readiness header')
    ready = Path(__file__).with_name('virtual-open-claim.h').read_text(encoding='utf-8')
    begin = ready.index(' /* A reset/main-down intent can arrive during the unlocked readback.')
    end = ready.index(' return radio->retired_serial', begin)
    if ready[:begin] + ready[end:] != files[ready_name].decode('utf-8').replace('\r\n', '\n'):
        p.error('Readiness header contains changes beyond reviewed demotion')
    ready_newline = '\r\n' if b'\r\n' in files[ready_name] else '\n'
    payloads[ready_name] = ready.replace('\n', ready_newline).encode('utf-8')
for relative, data in files.items():
    if (source / relative).read_bytes() != data:
        p.error('Source changed during preparation')
for relative, data in payloads.items():
    target = output / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
report = {'schema': 1, 'scope': 'v25b generation exhaustion and invalidated readiness deltas',
          'source_sha256': {n.as_posix(): digest(b) for n, b in files.items()},
          'candidate_sha256': {n.as_posix(): digest(b) for n, b in payloads.items()},
          'changed_files': [n.as_posix() for n in files if files[n] != payloads[n]], 'production_installed': False,
          'target_compiled': False, 'runtime_verified': False,
          'selective_txs_retirement_proved': False}
output.with_name(output.name + '-generation.json').write_text(json.dumps(report, indent=2)+'\n')
print('Prepared isolated v25b generation/readiness corrections; other files preserved')
