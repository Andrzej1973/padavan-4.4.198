#!/usr/bin/env python3
"""Compute exact-image service entrypoint-map coverage separately from classification."""


def active_service_entrypoint_map_status(active_include_selectors,
                                         selector_classes,
                                         service_entrypoints,
                                         checks):
    """Return whether every active service group has a mapped passing check."""
    active_groups = sorted({selector_classes[selector][1]
                            for selector in active_include_selectors
                            if selector in selector_classes
                            and selector_classes[selector][0] == 'service'})
    mapped_selectors_by_group = {
        service: set(selectors)
        for service, selectors, _ in service_entrypoints
    }
    mapped_groups = set(mapped_selectors_by_group)
    unmapped_groups = sorted(set(active_groups) - mapped_groups)
    missing_selectors = {
        group: sorted({selector for selector in active_include_selectors
                       if selector in selector_classes
                       and selector_classes[selector] == ('service', group)} -
                      mapped_selectors_by_group.get(group, set()))
        for group in active_groups
    }
    group_checks = {
        group: checks.get(group + '_selected_entrypoints_present_and_syntax_checked') is True
        for group in active_groups
    }
    return {
        'active_service_groups': active_groups,
        'unmapped_active_service_groups': unmapped_groups,
        'unmapped_active_service_selectors': missing_selectors,
        'active_service_entrypoint_checks': group_checks,
        'complete': (not unmapped_groups and
                     not any(missing_selectors.values()) and
                     all(group_checks.values())),
    }


def sfe_image_gate_status(enabled, image_paths, busybox_applets):
    """Check the compiled SFE entrypoint and modules without claiming runtime."""
    if not enabled:
        return {'status': 'not selected', 'passed': True}
    available_paths = set(image_paths)
    required_modules = {
        'fast-classifier.ko', 'shortcut-fe.ko',
        'shortcut-fe-ipv6.ko', 'shortcut-fe-cm.ko',
    }
    missing_modules = sorted(module for module in required_modules
        if not any(path.startswith('lib/modules/') and path.endswith('/' + module)
                   for path in available_paths))
    rc_present = 'sbin/rc' in available_paths
    modprobe_present = 'modprobe' in set(busybox_applets)
    return {
        'required_modules': sorted(required_modules),
        'missing_modules': missing_modules,
        'sbin_rc_present': rc_present,
        'busybox_modprobe_present': modprobe_present,
        'scope': 'selected-image rc/module/modprobe presence only; load, offload and throughput unverified',
        'passed': not missing_modules and rc_present and modprobe_present,
    }


def qos_image_gate_status(enabled, image_paths, kernel_config):
    """Check selected QoS userspace and configured kernel modules in ROMFS."""
    if not enabled:
        return {'status': 'not selected', 'passed': True}
    available_paths = set(image_paths)
    config = dict(kernel_config)
    required_core = {
        'CONFIG_IFB': 'm',
        'CONFIG_IMQ': 'm',
        'CONFIG_IMQ_BEHAVIOR_AB': 'y',
        'CONFIG_NETFILTER_XT_TARGET_IMQ': 'm',
    }
    bad_core = {key: {'expected': value, 'actual': config.get(key)}
                for key, value in required_core.items()
                if config.get(key) != value}
    module_names = {
        'CONFIG_IFB': 'ifb.ko',
        'CONFIG_IMQ': 'imq.ko',
        'CONFIG_NETFILTER_XT_TARGET_IMQ': 'xt_IMQ.ko',
        'CONFIG_NET_SCH_HTB': 'sch_htb.ko',
        'CONFIG_NET_SCH_HFSC': 'sch_hfsc.ko',
        'CONFIG_NET_SCH_TBF': 'sch_tbf.ko',
        'CONFIG_NET_SCH_INGRESS': 'sch_ingress.ko',
        'CONFIG_NET_CLS_TCINDEX': 'cls_tcindex.ko',
        'CONFIG_NET_CLS_ROUTE4': 'cls_route.ko',
        'CONFIG_NET_CLS_FW': 'cls_fw.ko',
        'CONFIG_NET_CLS_U32': 'cls_u32.ko',
        'CONFIG_NET_CLS_FLOW': 'cls_flow.ko',
        'CONFIG_NET_EMATCH_U32': 'em_u32.ko',
        'CONFIG_NET_ACT_MIRRED': 'act_mirred.ko',
        'CONFIG_NET_ACT_SKBEDIT': 'act_skbedit.ko',
    }
    required_modules = sorted({module_names[key] for key, value in config.items()
                               if value == 'm' and key in module_names})
    missing_modules = sorted(module for module in required_modules
        if not any(path.startswith('lib/modules/') and
                   path.rsplit('/', 1)[-1] == module
                   for path in available_paths))
    tc_paths = ('bin/tc',)
    found_tc = sorted(path for path in tc_paths if path in available_paths)
    return {
        'required_core_config': required_core,
        'invalid_core_config': bad_core,
        'required_modules': required_modules,
        'missing_modules': missing_modules,
        'tc_candidates': list(tc_paths),
        'tc_present': bool(found_tc),
        'tc_paths_found': found_tc,
        'scope': 'selected-image tc and configured IMQ/IFB/qdisc modules only; QoS activation, rules and throughput unverified',
        'passed': not bad_core and not missing_modules and bool(found_tc),
    }
