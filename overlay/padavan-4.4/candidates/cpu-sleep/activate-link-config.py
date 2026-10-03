#!/usr/bin/env python3
"""Select systick for an isolated kernel link candidate, not production firmware."""
import argparse
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('kernel', type=Path)
args = parser.parse_args()
kernel = args.kernel.resolve()
config = kernel / '.config'
kconfig = kernel / 'arch/mips/ralink/Kconfig'
if not config.is_file() or not kconfig.is_file() or 'config CLKEVT_MT7621_SYSTICK' not in kconfig.read_text():
    raise SystemExit('Prepare candidate hooks and copy effective config first')
lines = config.read_text().splitlines()
if 'CONFIG_SOC_MT7621=y' not in lines:
    raise SystemExit('Candidate must use effective MT7621 board config')
if 'CONFIG_GENERIC_CLOCKEVENTS_BROADCAST=y' not in lines:
    raise SystemExit('Broadcast timer support must be selected in the effective config')
tool = kernel / 'scripts/config'
if not tool.is_file():
    raise SystemExit('Kernel scripts/config missing')
subprocess.run(['bash', str(tool), '--file', str(config), '--enable', 'CLKEVT_MT7621_SYSTICK'], check=True)
selected = config.read_text().splitlines()
if selected.count('CONFIG_CLKEVT_MT7621_SYSTICK=y') != 1:
    raise SystemExit('scripts/config did not select exactly one systick candidate symbol')
print('Isolated link candidate symbol selected; run olddefconfig and verify it remains y before vmlinux build')
