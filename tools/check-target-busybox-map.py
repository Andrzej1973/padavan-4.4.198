#!/usr/bin/env python3
"""Prevent known selected-service selectors from disappearing from the image map."""
import ast
from pathlib import Path

source = Path(__file__).with_name('check-target-busybox.py')
tree = ast.parse(source.read_text(encoding='utf-8'))
mapping = next(ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign) and
               any(isinstance(target, ast.Name) and target.id == 'service_entrypoints'
                   for target in node.targets))
services = {name: (set(selectors), set(paths))
            for name, selectors, paths in mapping}
expected = {
    'shadowsocks_clients': (
        {'CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS'},
        {'usr/bin/ss-local', 'usr/bin/ss-redir'}),
    'wireguard_amneziawg': (
        {'CONFIG_FIRMWARE_INCLUDE_WIREGUARD', 'CONFIG_FIRMWARE_INCLUDE_AMNEZIAWG'},
        {'usr/bin/wireguard.sh', 'usr/bin/wgc.sh', 'usr/bin/wgs.sh'}),
    'wr_band_steering': (
        {'CONFIG_FIRMWARE_INCLUDE_WR_BAND_STEERING'},
        {'usr/sbin/wr-band-steering', 'usr/sbin/wr-band-steering-ctl', 'sbin/rc'}),
}
for name, (selectors, paths) in expected.items():
    if name not in services:
        raise SystemExit(f'FAIL BusyBox service map missing {name}')
    actual_selectors, actual_paths = services[name]
    if not selectors <= actual_selectors:
        raise SystemExit(f'FAIL {name} selector map missing: {sorted(selectors - actual_selectors)}')
    if not paths <= actual_paths:
        raise SystemExit(f'FAIL {name} image entrypoints missing: {sorted(paths - actual_paths)}')
print('PASS selected service map covers Shadowsocks clients, WireGuard/AmneziaWG and Band Steering')
