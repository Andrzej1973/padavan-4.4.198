#!/usr/bin/env python3
"""Check generated WireGuard status semantics against the pinned page input."""
import argparse
import sys
from pathlib import Path

p=argparse.ArgumentParser()
p.add_argument('page',type=Path)
a=p.parse_args()
sys.path.insert(0,str(Path(__file__).resolve().parent))
from legacy_ui import replace_legacy_wireguard_badge

source=a.page.read_text(encoding='utf-8')
result=replace_legacy_wireguard_badge(source)
start=result.index('function update_vpnc_status(vpnc_state){')
end=result.index('\nfunction applyRule()',start)
function=result[start:end]
assert "showhide_div('col_vpnc_wg_state', 0);" in function
assert 'vpnc_state == 1' not in function
assert 'vpnc_state == 2' not in function
assert "showhide_div('col_vpnc_state', (vpnc_state != 0" in function
assert '<#Connected#>' not in function
print('PASS WG/AWG legacy badge stays hidden; non-WG VPN state rendering is preserved')
