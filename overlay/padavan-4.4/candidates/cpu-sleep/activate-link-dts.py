#!/usr/bin/env python3
"""Activate systick only in the isolated WR1200JS kernel candidate DTS."""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('kernel', type=Path)
args = parser.parse_args()
kernel = args.kernel.resolve()
config = (kernel / '.config').read_text(encoding='utf-8')
for required in ('CONFIG_SOC_MT7621=y', 'CONFIG_CLKEVT_MT7621_SYSTICK=y',
                 'CONFIG_RALINK_BUILTIN_DTB_NAME="wr1200js"'):
    if required not in config.splitlines():
        raise SystemExit('Isolated WR1200JS configuration missing: ' + required)
directory = kernel / 'arch/mips/boot/dts/ralink'
board = directory / 'wr1200js.dts'
source = board.read_text(encoding='utf-8')
soc = (directory / 'mt7621.dtsi').read_text(encoding='utf-8')
if '#include "mt7621.dtsi"' not in source or 'cpuintc:' not in soc:
    raise SystemExit('Inspect the MT7621 include and CPU interrupt controller')
if not re.search(r'#address-cells\s*=\s*<1>;', soc) or not re.search(r'#size-cells\s*=\s*<1>;', soc):
    raise SystemExit('Inspect register address/size cell format')
if 'mt7621-systick' in source or 'timer@1e000500' in source:
    raise SystemExit('Systick candidate already present; refuse duplicate activation')
fragment = '''
/* Isolated CPU_SLEEP link candidate; never copied into the main image tree. */
/ {
    wr1200js_sleep_systick: timer@1e000500 {
        compatible = "mediatek,mt7621-systick", "ralink,cevt-systick";
        reg = <0x1e000500 0x0c>, <0x1e000410 0x04>;
        reg-names = "counter", "sleep-control";
        interrupt-parent = <&cpuintc>;
        interrupts = <7>;
        status = "okay";
    };
};
'''
board.write_text(source.rstrip() + '\n' + fragment, encoding='utf-8')
print('Isolated systick Device Tree activated; build/IRQ/divider/SMP runtime verification remains required')
