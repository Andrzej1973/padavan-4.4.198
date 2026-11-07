#!/usr/bin/env python3
"""Synthetic provenance controls; no target compilation or runtime claim."""
import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile

compiler = shutil.which('gcc')
if not compiler:
    raise SystemExit('Host gcc required')
script = Path(__file__).with_name('check-channel-target-config.py').resolve()
with tempfile.TemporaryDirectory(prefix='wr-channel-target-controls-') as temp:
    root = Path(temp)
    driver = root / 'driver'
    manifest = root / 'manifest.json'
    paths = {'mt7603': 'chips/mt7603.c', 'cmm_asic_mt': 'hw_ctrl/cmm_asic_mt.c',
             'ap_autoChSel': 'ap/ap_autoChSel.c', 'rtmp_init_inf': 'common/rtmp_init_inf.c'}
    hashes = {}
    for unit, relative in paths.items():
        source = driver / relative
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text('#define MT7603 1\n#define MT_MAC 1\n#define RTMP_PCI_SUPPORT 1\n')
        hashes[relative] = hashlib.sha256(source.read_bytes()).hexdigest()
        # Only a synthetic ELF header: tests parser refusal, never proves code generation.
        source.with_suffix('.o').write_bytes(b'\x7fELF\x01\x01' + bytes(10) + b'\x01\x00\x08\x00')
        (driver / ('.' + unit + '.o.cmd')).write_text(
            'cmd_fixture := ' + shlex.quote(str(Path(compiler).resolve())) +
            ' -c -o ignored.o ' + shlex.quote(str(source)) + '\n')
    manifest.write_text(json.dumps({'merged_driver_sha256': hashes}))
    args = [sys.executable, str(script), '--kernel', str(root), '--driver', str(driver),
            '--compiler', compiler, '--manifest', str(manifest),
            '--output', str(root / 'result.json')]

    def run(ok):
        result = subprocess.run(args, capture_output=True, text=True)
        assert (result.returncode == 0) == ok, (result.stdout, result.stderr)

    run(True)
    source = driver / paths['mt7603']
    original = source.read_bytes()
    source.write_text('#define MT_MAC 1\n#define RTMP_PCI_SUPPORT 1\n')
    run(False)  # Missing MT7603 must fail, even if other driver guards exist.
    source.write_bytes(original + b'\n')
    run(False)  # Same effective macros, wrong source digest.
    source.write_bytes(original)
    obj = source.with_suffix('.o')
    header = obj.read_bytes()
    obj.write_bytes(header[:18] + b'\x3e\x00')
    run(False)  # x86-64 cannot pass the MIPS object requirement.
    obj.write_bytes(header)
    command = driver / '.mt7603.o.cmd'
    saved = command.read_bytes()
    command.unlink()
    run(False)
    command.write_bytes(saved)
    run(True)
print('PASS synthetic channel provenance controls: missing guard, source drift, wrong machine, missing Kbuild command; temporary fixtures removed; not target evidence')
