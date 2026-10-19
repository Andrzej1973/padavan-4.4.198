#!/usr/bin/env python3
"""Prevent known selected-service selectors from disappearing from the image map."""
import ast
from pathlib import Path
from target_busybox_service_map import (
    active_service_entrypoint_map_status,
    qos_image_gate_status,
    sfe_image_gate_status,
)

source = Path(__file__).with_name('check-target-busybox.py')
tree = ast.parse(source.read_text(encoding='utf-8'))
mapping = next(ast.literal_eval(node.value) for node in tree.body
               if isinstance(node, ast.Assign) and
               any(isinstance(target, ast.Name) and target.id == 'service_entrypoints'
                   for target in node.targets))
services = {name: (set(selectors), set(paths))
            for name, selectors, paths in mapping}
classifier = next(ast.literal_eval(node.value) for node in tree.body
                  if isinstance(node, ast.Assign) and
                  any(isinstance(target, ast.Name) and target.id == 'selector_classes'
                      for target in node.targets))
dispatches = next(ast.literal_eval(node.iter) for node in ast.walk(tree)
                  if isinstance(node, ast.For) and isinstance(node.target, ast.Tuple)
                  and [item.id for item in node.target.elts if isinstance(item, ast.Name)]
                      == ['service', 'selector', 'script_name'])
expected = {
    'shadowsocks_clients': (
        {'CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS', 'CONFIG_FIRMWARE_INCLUDE_SSREDIR',
         'CONFIG_FIRMWARE_INCLUDE_SSLOCAL'},
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

# Selector classification and an actual service-entrypoint map are separate
# properties. Guard the report field against accidentally reverting to the
# former as a proxy for the latter.
map_complete_assignment = next((node for node in ast.walk(tree)
    if isinstance(node, ast.Assign) and any(
        isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
        and target.value.id == 'report'
        and isinstance(target.slice, ast.Constant)
        and target.slice.value == 'selected_service_entrypoint_map_complete'
        for target in node.targets)), None)
if map_complete_assignment is None or ast.unparse(map_complete_assignment.value) != \
        "service_map['complete']":
    raise SystemExit('FAIL selected_service_entrypoint_map_complete must report actual active service maps')
active = {line.split('=', 1)[0] for line in Path('configs.build/wr1200js.config')
          .read_text(encoding='utf-8').splitlines()
          if line.startswith('CONFIG_FIRMWARE_INCLUDE_') and line.endswith('=y')}
required_groups = {group for selector, (kind, group) in classifier.items()
                   if selector in active and kind == 'service'}
active_selectors_by_group = {}
for selector in active:
    kind_group = classifier.get(selector)
    if kind_group and kind_group[0] == 'service':
        active_selectors_by_group.setdefault(kind_group[1], set()).add(selector)
mapped_groups = set(services)
missing_groups = required_groups - mapped_groups
if missing_groups:
    raise SystemExit('FAIL active service selectors lack entrypoint maps: ' +
                     ', '.join(sorted(missing_groups)))
for group, selectors in active_selectors_by_group.items():
    mapped_selectors, paths = services[group]
    if not selectors <= mapped_selectors:
        raise SystemExit(f'FAIL {group} map omits active selectors: ' +
                         ', '.join(sorted(selectors - mapped_selectors)))
    if not paths:
        raise SystemExit(f'FAIL {group} active-service map has no image paths')
all_service_checks = {group + '_selected_entrypoints_present_and_syntax_checked': True
                      for group in required_groups}
complete = active_service_entrypoint_map_status(active, classifier,
    [(group, tuple(selectors), tuple(paths))
     for group, (selectors, paths) in services.items()], all_service_checks)
if not complete['complete']:
    raise SystemExit('FAIL complete synthetic active-service map was rejected')
missing_map = active_service_entrypoint_map_status(active, classifier,
    [(group, tuple(selectors), tuple(paths)) for group, (selectors, paths) in services.items()
     if group != next(iter(required_groups))],
    all_service_checks)
if missing_map['complete'] or not missing_map['unmapped_active_service_groups']:
    raise SystemExit('FAIL a missing active-service map was accepted')
missing_selector_group = next(iter(required_groups))
incomplete_selector_maps = [(group,
    tuple(selector for selector in selectors if selector not in active_selectors_by_group.get(group, set())),
    tuple(paths)) for group, (selectors, paths) in services.items()]
incomplete_selector_status = active_service_entrypoint_map_status(
    active, classifier, incomplete_selector_maps, all_service_checks)
if incomplete_selector_status['complete'] or not any(
        incomplete_selector_status['unmapped_active_service_selectors'].values()):
    raise SystemExit('FAIL an active selector missing from its group map was accepted')
missing_check = dict(all_service_checks)
missing_check.pop(next(iter(required_groups)) + '_selected_entrypoints_present_and_syntax_checked')
if active_service_entrypoint_map_status(active, classifier,
        [(group, tuple(selectors), tuple(paths)) for group, (selectors, paths) in services.items()],
        missing_check)['complete']:
    raise SystemExit('FAIL an absent active-service image check was accepted')
failed_check = dict(all_service_checks)
failed_check[next(iter(required_groups)) + '_selected_entrypoints_present_and_syntax_checked'] = False
if active_service_entrypoint_map_status(active, classifier,
        [(group, tuple(selectors), tuple(paths)) for group, (selectors, paths) in services.items()],
        failed_check)['complete']:
    raise SystemExit('FAIL a failed active-service image check was accepted')
print(f'PASS {len(required_groups)} active-service maps; missing-map, omitted-selector, missing-check and failed-check fixtures reject completion')

for alias_selectors in ({'CONFIG_FIRMWARE_INCLUDE_SSLOCAL'},
                        {'CONFIG_FIRMWARE_INCLUDE_SSREDIR'},
                        {'CONFIG_FIRMWARE_INCLUDE_SSLOCAL', 'CONFIG_FIRMWARE_INCLUDE_SSREDIR'},
                        {'CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS'}):
    alias_map = active_service_entrypoint_map_status(alias_selectors, classifier,
        mapping, {'shadowsocks_clients_selected_entrypoints_present_and_syntax_checked': True})
    if not alias_map['complete'] or alias_map['active_service_groups'] != ['shadowsocks_clients']:
        raise SystemExit('FAIL requested/effective Shadowsocks selector normalization loses the service group')
print('PASS both requested Shadowsocks aliases and the effective package selector require the same service map')

sfe_modules = {'fast-classifier.ko', 'shortcut-fe.ko',
               'shortcut-fe-ipv6.ko', 'shortcut-fe-cm.ko'}
sfe_paths = {'sbin/rc'} | {
    'lib/modules/4.4.198/kernel/net/shortcut-fe/' + name
    for name in sfe_modules
}
if not sfe_image_gate_status(True, sfe_paths, {'modprobe'})['passed']:
    raise SystemExit('FAIL complete SFE image entrypoints were rejected')
missing_sfe_paths = ['sbin/rc'] + [
    'lib/modules/4.4.198/kernel/net/shortcut-fe/' + name
    for name in sfe_modules
]
for missing_path in missing_sfe_paths:
    if sfe_image_gate_status(True, sfe_paths - {missing_path}, {'modprobe'})['passed']:
        raise SystemExit(f'FAIL incomplete SFE image accepted without {missing_path}')
if sfe_image_gate_status(True, sfe_paths, set())['passed']:
    raise SystemExit('FAIL SFE image accepted without BusyBox modprobe')
if not sfe_image_gate_status(False, set(), set())['passed']:
    raise SystemExit('FAIL unselected SFE feature was treated as a missing image entrypoint')
print('PASS SFE exact-image gate requires rc, all four Shortcut FE modules and BusyBox modprobe; rejects each missing condition')

qos_config = {
    'CONFIG_IFB': 'm', 'CONFIG_IMQ': 'm',
    'CONFIG_IMQ_BEHAVIOR_AB': 'y',
    'CONFIG_NETFILTER_XT_TARGET_IMQ': 'm',
    'CONFIG_NET_SCH_HTB': 'm', 'CONFIG_NET_SCH_HFSC': 'm',
    'CONFIG_NET_SCH_TBF': 'm', 'CONFIG_NET_SCH_INGRESS': 'm',
    'CONFIG_NET_CLS_TCINDEX': 'm', 'CONFIG_NET_CLS_ROUTE4': 'm',
    'CONFIG_NET_CLS_FW': 'm', 'CONFIG_NET_CLS_U32': 'm',
    'CONFIG_NET_CLS_FLOW': 'm', 'CONFIG_NET_EMATCH_U32': 'm',
    'CONFIG_NET_ACT_MIRRED': 'm', 'CONFIG_NET_ACT_SKBEDIT': 'm',
}
qos_modules = {'ifb.ko', 'imq.ko', 'xt_IMQ.ko', 'sch_htb.ko',
    'sch_hfsc.ko', 'sch_tbf.ko', 'sch_ingress.ko', 'cls_tcindex.ko',
    'cls_route.ko', 'cls_fw.ko', 'cls_u32.ko', 'cls_flow.ko',
    'em_u32.ko', 'act_mirred.ko', 'act_skbedit.ko'}
qos_paths = {'bin/tc'} | {
    'lib/modules/4.4.198/kernel/net/sched/' + name for name in qos_modules
}
if not qos_image_gate_status(True, qos_paths, qos_config)['passed']:
    raise SystemExit('FAIL complete QoS image entrypoints were rejected')
for missing_path in qos_paths:
    if qos_image_gate_status(True, qos_paths - {missing_path}, qos_config)['passed']:
        raise SystemExit(f'FAIL incomplete QoS image accepted without {missing_path}')
for key, wrong_value in (('CONFIG_IFB', 'n'),
                         ('CONFIG_IMQ_BEHAVIOR_AB', 'n'),
                         ('CONFIG_NETFILTER_XT_TARGET_IMQ', 'n')):
    bad_config = dict(qos_config)
    bad_config[key] = wrong_value
    if qos_image_gate_status(True, qos_paths, bad_config)['passed']:
        raise SystemExit(f'FAIL QoS image accepted with invalid {key}={wrong_value}')
if not qos_image_gate_status(False, set(), {})['passed']:
    raise SystemExit('FAIL unselected QoS was treated as a missing image entrypoint')
if qos_image_gate_status(True, qos_paths - {'bin/tc'} | {'usr/sbin/tc'}, qos_config)['passed']:
    raise SystemExit('FAIL QoS tc at a path different from the pinned recipe was accepted')
if qos_image_gate_status(True, {path.replace('xt_IMQ.ko', 'xt_imq.ko')
        for path in qos_paths}, qos_config)['passed']:
    raise SystemExit('FAIL Linux case-sensitive module path was ignored')
print('PASS QoS exact-image gate requires tc, selected IMQ/IFB/qdisc modules and core config; rejects every missing file and invalid core symbol')

# Guard exhaustive classification against every active firmware INCLUDE selector.
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
