#!/usr/bin/env python3
"""Evaluate actual switch headers with the effective config, never touch hardware."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import tempfile

p = argparse.ArgumentParser()
p.add_argument('--kernel-config', type=Path, required=True)
p.add_argument('--header', type=Path, required=True)
p.add_argument('--output', type=Path, required=True)
p.add_argument('--compiler', default='gcc')
a = p.parse_args()
config = a.kernel_config.read_text()
defines = []
for key, value in re.findall(r'^(CONFIG_\w+)=(.+)$', config, re.M):
    if not re.fullmatch(r'CONFIG_(RAETH_ESW_PORT_\w+|MT7530_GSW|P4_\w+|P5_\w+|GE2_\w+|RAETH_GMAC2)', key):
        continue
    if value == 'y': value = '1'
    elif not re.fullmatch(r'-?(?:[0-9]+|0x[0-9a-fA-F]+)', value): continue
    defines.append(f'#define {key} {value}')
header = a.header.resolve()
planner = Path(__file__).with_name('plan.h').resolve()
source = '#include <stdio.h>\n#include <stdint.h>\ntypedef uint8_t u8;\ntypedef uint16_t u16;\ntypedef uint32_t u32;\n'
source += '\n'.join(defines) + '\n'
source += '#include ' + json.dumps(header.as_posix()) + '\n'
source += '#include ' + json.dumps(planner.as_posix()) + '\n'
source += r'''
int main(void) {
 struct wr_wan_port_board board={WAN_PORT_X,{LAN_PORT_1,LAN_PORT_2,LAN_PORT_3,LAN_PORT_4}};
 struct wr_wan_port_plan plan;unsigned choice;
 printf("{\"original_wan\":%u,\"lan\":[%u,%u,%u,%u],\"cpu_lan\":%u,\"cpu_wan\":%u,",
 (unsigned)WAN_PORT_X,(unsigned)LAN_PORT_1,(unsigned)LAN_PORT_2,(unsigned)LAN_PORT_3,(unsigned)LAN_PORT_4,
 (unsigned)LAN_PORT_CPU,(unsigned)WAN_PORT_CPU);
 printf("\"lan_mask\":%u,\"wan_mask\":%u,\"cpu_lan_mask\":%u,\"cpu_wan_mask\":%u,\"excluded\":%u,\"selections\":[",
 (unsigned)MASK_LAN_PORTS_ALL,(unsigned)MASK_WAN_PORT_X,(unsigned)MASK_LAN_PORT_CPU,
 (unsigned)MASK_WAN_PORT_CPU,(unsigned)ESW_MASK_EXCLUDE);
 for(choice=0;choice<5;choice++) {
  if(!wr_wan_port_plan(&board,choice,&plan))return 2;
  printf("%s{\"selection\":%u,\"wan_phy\":%u,\"wan_external\":%u,\"lan_external\":%u,\"isolated_external\":%u}",
   choice?",":"",choice,plan.wan_phy,plan.wan_external,plan.lan_external,plan.isolated_external);
 }
 puts("]}");return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-wan-topology-') as directory:
    stage = Path(directory)
    code, binary = stage/'topology.c', stage/'topology'
    code.write_text(source)
    subprocess.run([a.compiler, '-std=gnu99', '-Wall', '-Wextra', '-Werror', str(code), '-o', str(binary)], check=True)
    topology = json.loads(subprocess.check_output([str(binary)], text=True, timeout=5))
external = topology['wan_mask'] | topology['lan_mask']
if external & (topology['cpu_lan_mask'] | topology['cpu_wan_mask']):
    raise SystemExit('External and CPU masks overlap; topology unsupported by external-port planner')
topology.update(schema=1, source_only=True, runtime_verified=False,
    kernel_config_sha256=hashlib.sha256(a.kernel_config.read_bytes()).hexdigest(),
    driver_header_sha256=hashlib.sha256(header.read_bytes()).hexdigest(),
    common_header_sha256=hashlib.sha256(header.with_name('esw_common.h').read_bytes()).hexdigest(),
    limits='Host evaluation of actual driver definitions only; not switch programming, physical port identification or WAN connectivity.')
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(topology, indent=2) + '\n')
print('PASS source switch topology and five external-port plans; runtime unverified')
