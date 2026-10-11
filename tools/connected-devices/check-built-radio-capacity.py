"""Probe capacity using flags from the kernel's actual compiled object records."""
import argparse
import json
import re
import subprocess
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('--compiler', required=True, type=Path)
p.add_argument('--output', required=True, type=Path)
a = p.parse_args()
kernel = a.source / 'trunk/linux-4.4.x'
config = (kernel / '.config').read_text(encoding='utf-8')
selector = re.findall(r'^CONFIG_RT_MAX_CLIENTS=(\d+)$', config, re.M)
if selector != ['64']:
    raise SystemExit('Unexpected WR kernel client selector')
allowed = {'MT7603', 'MT76x2', 'BB_SOC', 'MT7603_FPGA', 'MT7628_FPGA',
           'MT7636_FPGA', 'MAC_REPEATER_SUPPORT', 'MULTI_APCLI_SUPPORT',
           'ECONET_ALPHA_RELEASE', 'CONFIG_RT_MAX_CLIENTS'}
result = {}
work = a.output.parent
work.mkdir(parents=True, exist_ok=True)
for radio in ('mt76x2', 'mt76x3'):
    directory = kernel / 'drivers/net/wireless/mediatek' / radio
    records = list(directory.rglob('.cmm_info.o.cmd'))
    if len(records) != 1:
        raise SystemExit(f'{radio}: require one actual cmm_info object command')
    flags = []
    for token in re.findall(r'(?:^|\s)(-D[^\s]+)', records[0].read_text(encoding='utf-8')):
        if token[2:].split('=', 1)[0] in allowed:
            flags.append(token)
    flags.append('-DCONFIG_RT_MAX_CLIENTS=64')
    if radio == 'mt76x3' and '-DMT7603' not in flags:
        raise SystemExit('MT7603 chipset flag missing from actual object command')
    text = (directory / 'include/oid.h').read_text(encoding='utf-8')
    anchor = '#ifdef CONFIG_RT_MAX_CLIENTS' if radio == 'mt76x2' else '#ifdef BB_SOC'
    if text.count(anchor) != 1 or text.count('#define MAX_NUMBER_OF_ACL') != 1:
        raise SystemExit(f'{radio}: capacity anchors changed')
    block = text[text.index(anchor):text.index('#define MAX_NUMBER_OF_ACL')]
    probe = work / f'{radio}-actual-capacity.c'
    assertion = 'MAX_NUMBER_OF_MAC == 64' if radio == 'mt76x2' else '(MAX_NUMBER_OF_MAC == 75 || MAX_NUMBER_OF_MAC == 58 || MAX_NUMBER_OF_MAC == 41)'
    probe.write_text(block + '\n_Static_assert(' + assertion + ', "unsupported station export capacity");\nunsigned char wr_capacity[MAX_NUMBER_OF_MAC];\n', encoding='utf-8')
    subprocess.run([str(a.compiler.resolve()), '-std=c11', '-mips32r2', '-mabi=32',
                    '-msoft-float', *flags, '-c', str(probe.resolve()), '-o',
                    str((work / f'{radio}-actual-capacity.o').resolve())], check=True)
    out = subprocess.run([str(a.compiler.resolve()), '-E', '-P', *flags, str(probe.resolve())],
                         check=True, capture_output=True, text=True).stdout
    expression = re.findall(r'wr_capacity\[([^\]]+)\]', out)
    # Retain the compiler-expanded expression as evidence; do not eval source text.
    if len(expression) != 1:
        raise SystemExit(f'{radio}: missing compiler capacity expression')
    result[radio] = {'object_command': str(records[0]), 'capacity_expression': expression[0],
                     'flags': flags}
a.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
