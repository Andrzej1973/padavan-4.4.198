#!/usr/bin/env python3
"""Prepare a separate pinned kernel tree for full candidate linking.

The CI link probe calls this only on a separate copied kernel directory after
the production firmware artifact has been uploaded. Do not target that image's
original kernel tree.
"""
import argparse
from pathlib import Path
import shutil

parser = argparse.ArgumentParser()
parser.add_argument('kernel', type=Path)
args = parser.parse_args()
kernel = args.kernel.resolve()
payload = Path(__file__).resolve().parent
if not (kernel / 'arch/mips/ralink/timer-gic.c').is_file():
    raise SystemExit('Target is not the expected vendor MIPS kernel')

timer = kernel / 'arch/mips/ralink/timer-gic.c'
text = timer.read_text()
anchor = '\tof_clk_init(NULL);\n\tclocksource_probe();'
if text.count(anchor) != 1:
    raise SystemExit('Unexpected platform time initialization')
if 'mt7621_systick_early_init' in text:
    raise SystemExit('Candidate already applied')
if text.count('void __init plat_time_init(void)') != 1:
    raise SystemExit('Unexpected platform timer entry point')
text = text.replace('void __init plat_time_init(void)', '#ifdef CONFIG_CLKEVT_MT7621_SYSTICK\nvoid __init mt7621_systick_early_init(void);\n#endif\n\nvoid __init plat_time_init(void)')
text = text.replace(anchor, '\tof_clk_init(NULL);\n#ifdef CONFIG_CLKEVT_MT7621_SYSTICK\n\tmt7621_systick_early_init();\n#endif\n\tclocksource_probe();')

makefile = kernel / 'arch/mips/ralink/Makefile'
make_text = makefile.read_text()
if 'cevt-mt7621.o' in make_text:
    raise SystemExit('Unexpected existing candidate Makefile hook')
kconfig = kernel / 'arch/mips/ralink/Kconfig'
config_text = kconfig.read_text()
if 'config CLKEVT_MT7621_SYSTICK' in config_text:
    raise SystemExit('Unexpected existing candidate Kconfig hook')

files = {'cevt-mt7621-draft.c': 'arch/mips/ralink/cevt-mt7621.c',
         'cevt-r4k-draft.c': 'arch/mips/kernel/cevt-r4k.c',
         'csrc-r4k-draft.c': 'arch/mips/kernel/csrc-r4k.c',
         'mips-gic-timer-draft.c': 'drivers/clocksource/mips-gic-timer.c'}
for source, destination in files.items():
    if not (payload / source).is_file() or not (kernel / destination).parent.is_dir():
        raise SystemExit('Missing candidate or destination: ' + source)
draft_kconfig = (payload / 'Kconfig.draft').read_text()
if 'config CLKEVT_MT7621_SYSTICK' not in draft_kconfig:
    raise SystemExit('Missing systick Kconfig definition')
for source, destination in files.items():
    shutil.copyfile(payload / source, kernel / destination)
timer.write_text(text)
makefile.write_text(make_text + '\nobj-$(CONFIG_CLKEVT_MT7621_SYSTICK) += cevt-mt7621.o\n')
kconfig.write_text(config_text + '\n' + draft_kconfig)
print('Candidate sources and link hooks prepared; config and DTS still require explicit activation')
