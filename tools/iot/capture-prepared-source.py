#!/usr/bin/env python3
"""Capture selected manifest-verified candidate source inputs for diagnostics.

Usage: capture-prepared-source.py MANIFEST DRIVER OUTPUT
Source/host evidence only; compilation and runtime are verified separately.
"""
import hashlib, json, pathlib, sys
manifest = json.load(open(sys.argv[1], encoding='utf-8'))
driver = pathlib.Path(sys.argv[2])
snapshot = pathlib.Path(sys.argv[3])
selected = {
    'mac/mt_mac.c', 'tx_rx/txs.c', 'common/cmm_data_pci.c',
    'ap/ap_connect.c', 'ap/ap_mbss.c', 'hw_ctrl/cmm_asic_mt.c',
    'include/wr-iot-beacon-producer-kernel.h',
    'include/ra2-software-off.h', 'include/beacon-filter-owner-kernel.h',
}
captured = {}
captured_bytes = 0
if manifest['target_compiled'] or manifest['production_installed']:
    raise SystemExit('Candidate manifest makes an unsupported claim')
for name, expected in manifest['candidate_driver_sha256'].items():
    path = driver / name
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != expected:
        raise SystemExit('Isolated source copy mismatch: ' + name)
    if name in selected:
        captured_bytes += len(data)
        if captured_bytes > 6 * 1024 * 1024:
            raise SystemExit('Focused prepared-source snapshot exceeds budget')
        target = snapshot / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        captured[name] = {'sha256': expected, 'bytes': len(data)}
snapshot.mkdir(parents=True, exist_ok=True)
(snapshot / 'index.json').write_text(json.dumps({
    'scope': 'Hash-checked prepared source inputs; compilation/runtime recorded separately',
    'files': captured, 'bytes': captured_bytes,
}, indent=2) + '\n', encoding='utf-8')