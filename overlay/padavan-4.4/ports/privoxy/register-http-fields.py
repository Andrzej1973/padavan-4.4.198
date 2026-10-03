#!/usr/bin/env python3
"""Privoxy HTTP fields for the extended event bank; UI/file routing still separate."""
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('httpd', type=Path)
args = parser.parse_args()
common = args.httpd / 'common.h'
variables = args.httpd / 'variables.c'
c = common.read_text(encoding='utf-8')
v = variables.read_text(encoding='utf-8')
if 'event_mask_extended' not in c or 'EVMX_RESTART_PRIVOXY' in c or 'privoxy_enable' in v:
    raise SystemExit('Inspect extended bank/Privoxy registration')
pos = c.rfind('#endif')
if pos < 0:
    raise SystemExit('Missing header guard')
c = c[:pos] + '\n#define EVMX_RESTART_PRIVOXY (1ULL << 0)\n#define EVT_RESTART_PRIVOXY 2\n\n' + c[pos:]
anchor = '\tstruct variable variables_LANHostConfig[] = {\n'
if v.count(anchor) != 1:
    raise SystemExit('Inspect field table')
fields = '#if defined(APP_PRIVOXY)\n'
for name in ['privoxy_enable', 'privoxy.config', 'privoxy.user.action', 'privoxy.user.filter', 'privoxy.user.trust']:
    kind = '' if name == 'privoxy_enable' else 'File'
    fields += '\t\t\t{"' + name + '", "' + kind + '", NULL, EVM_BLOCK_UNSAFE, EVMX_RESTART_PRIVOXY},\n'
fields += '#endif\n'
v = v.replace(anchor, anchor + fields, 1)
anchor = '\t\t{EVM_RESTART_FIREWALL,\t\tEVT_RESTART_FIREWALL,\t\tRCN_RESTART_FIREWALL,\t0},'
if v.count(anchor) != 1:
    raise SystemExit('Inspect event table anchor')
event = '#if defined(APP_PRIVOXY)\n\t\t{0, EVT_RESTART_PRIVOXY, "restart_privoxy", EVM_RESTART_FIREWALL, EVMX_RESTART_PRIVOXY, 0},\n#endif\n'
v = v.replace(anchor, event + anchor, 1)
common.write_text(c, encoding='utf-8')
variables.write_text(v, encoding='utf-8')
print('Privoxy HTTP fields/event registered; file routing/UI checks pending')
