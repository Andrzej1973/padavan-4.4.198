#!/usr/bin/env python3
"""Prepare the complete steering source sequence before the normal build.

Not yet called by production CI. Failed preparation must abort the build;
discard that source checkout rather than continuing from partial patches.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--config', type=Path, required=True)
p.add_argument('--compiler', type=Path, required=True)
a = p.parse_args()
lines = a.config.read_text(encoding='utf-8').splitlines()
if lines.count('CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING=y') != 1:
    raise SystemExit('Explicit steering build selector required; no preparation performed')
if lines.count('CONFIG_FIRMWARE_PRODUCT_ID="WR1200JS"') != 1:
    raise SystemExit('Complete steering integration supports WR1200JS only')
root = a.source.resolve()
compiler = a.compiler.resolve()
if not compiler.is_file() or not os.access(compiler, os.X_OK):
    raise SystemExit('Executable target compiler required before preparation')
marker = root / 'band-steering-source-integration.json'
abi = root / 'band-steering-source-abi'
if marker.exists() or abi.exists():
    raise SystemExit('Source integration already attempted; use a fresh checkout')
tools = Path(__file__).parent.resolve()
report = {'preparation_complete': False, 'production_installed': False,
          'runtime_verified': False, 'factory_enabled': False, 'steps': []}
def save():
    marker.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
def run(name, *arguments):
    subprocess.run([sys.executable, '-X', 'utf8', str(tools / name),
                    *map(str, arguments)], check=True)
    report['steps'].append(name)
    save()
save()
for name in ('prepare-idle-aging.py', 'prepare-grant-readback.py',
             'prepare-wps-guards.py', 'prepare-channel-stats.py',
             'prepare-main-bss.py', 'prepare-off-ack.py',
             'prepare-uninitialized-off.py', 'prepare-nvram-snapshot.py',
             'prepare-profile-integration.py', 'prepare-child-reaper.py',
             'prepare-wifi-lifecycle.py', 'prepare-profile-snapshot.py',
             'prepare-wifi-snapshot.py', 'prepare-radio-snapshot.py',
             'prepare-board-defaults.py'):
    run(name, root)
run('prepare-abi-probe.py', root, '--output', abi)
for radio in ('mt76x2', 'mt76x3'):
    subprocess.run([str(compiler), '-std=gnu11', '-mips32r2', '-mabi=32',
                    '-msoft-float', '-O2', '-c', str(abi / (radio+'-abi.c')),
                    '-o', str(abi / (radio+'-abi.o'))], check=True)
run('read-abi-probe.py', abi)
run('prepare-package-integration.py', root, '--layout', abi / 'protocol-layout.h')
report['preparation_complete'] = True
save()
print('Complete source preparation succeeded; image compilation and runtime remain unverified')
