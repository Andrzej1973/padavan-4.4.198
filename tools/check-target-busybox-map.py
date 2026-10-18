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
dispatches = next(ast.literal_eval(node.iter) for node in ast.walk(tree)
                  if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)
                  and [item.id for item in node.target.elts if isinstance(item, ast.Name)]
                      == ['service', 'selector', 'script_name'])
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
    'u2ec': (
        {'CONFIG_FIRMWARE_INCLUDE_U2EC'},
        {'usr/sbin/u2ec'}),
}
for name, (selectors, paths) in expected.items():
    if name not in services:
        raise SystemExit(f'FAIL BusyBox service map missing {name}')
    actual_selectors, actual_paths = services[name]
    if not selectors <= actual_selectors:
        raise SystemExit(f'FAIL {name} selector map missing: {sorted(selectors - actual_selectors)}')
    if not paths <= actual_paths:
        raise SystemExit(f'FAIL {name} image entrypoints missing: {sorted(paths - actual_paths)}')
if ('vlmcsd', 'CONFIG_FIRMWARE_INCLUDE_VLMCSD', 'vlmcsd.sh') not in dispatches:
    raise SystemExit('FAIL KMS invalid-action BusyBox probe missing')
print('PASS selected-service map covers Shadowsocks, WireGuard/AmneziaWG and Band Steering; KMS dispatcher has a safe refusal probe')

# Guard exhaustive classification against every active firmware INCLUDE selector.
classifier = next(ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign) and
                  any(isinstance(target, ast.Name) and target.id == 'selector_classes'
                      for target in node.targets))
config = Path('configs.build/wr1200js.config').read_text(encoding='utf-8').splitlines()
active = {line.split('=', 1)[0] for line in config
          if line.startswith('CONFIG_FIRMWARE_INCLUDE_') and line.endswith('=y')}
missing = sorted(active - set(classifier))
if missing:
    raise SystemExit(f'FAIL active WR1200JS selectors lack an audit class: {missing}')
print(f'PASS all {len(active)} active WR1200JS INCLUDE selectors have explicit service/component classification')

workflow = Path('.github/workflows/build-padavan-4.4-wr1200js.yml').read_text(encoding='utf-8')
wpad_step = workflow.find('python3 overlay/padavan-4.4/scripts/verify-wpad.py')
zram_step = workflow.find('python3 tools/verify-zram-image.py padavan-4.4 | tee zram-image-checks.txt')
busybox_step = workflow.find('python3 tools/check-target-busybox.py padavan-4.4 --output target-busybox-audit.json')
if wpad_step < 0 or zram_step < 0 or busybox_step < 0 or max(wpad_step,zram_step) >= busybox_step:
    raise SystemExit('FAIL WPAD and ZRAM exact-image reports must be generated before the BusyBox audit consumes them')
print('PASS WPAD and ZRAM final-ROMFS verifiers run before the exact-image BusyBox audit')
