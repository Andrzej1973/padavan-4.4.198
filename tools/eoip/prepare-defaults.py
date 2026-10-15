#!/usr/bin/env python3
"""Add EoIP requested-state defaults only when the package is selected.

No existing NVRAM is rewritten by this build transformation. RC and WebUI
integration are separate; merely shipping a profile must not start a tunnel.
"""
import argparse
from pathlib import Path


def prepare(source: Path, config: Path) -> None:
    if 'CONFIG_FIRMWARE_INCLUDE_EOIP=y' not in config.read_text().splitlines():
        print('EoIP not selected; defaults unchanged')
        return
    user = source / 'trunk/user'
    fields = {
        'enable': '0', 'autostart': '0', 'local': '0.0.0.0',
        'remote': '', 'id': '0', 'mtu': '1458', 'keepalive': '0',
        'retries': '0', 'bridge': '',
    }
    defaults = [('eoip_enable', '0')]
    defaults += [(f'eoip_slot{slot}_{key}', value)
                 for slot in range(8) for key, value in fields.items()]
    block = '#if defined(APP_EOIP)\n'
    block += ''.join(f'\t{{ "{key}", "{value}" }},\n' for key, value in defaults)
    block += '#endif\n\n'
    changes = [
        (user / 'shared/cflags.mk', 'ifeq ($(CONFIG_FIRMWARE_INCLUDE_IPERF3),y)\n',
         'ifeq ($(CONFIG_FIRMWARE_INCLUDE_EOIP),y)\nCFLAGS += -DAPP_EOIP\nendif\n\n'),
        (user / 'shared/defaults.c', '#if defined (APP_IPERF3)\n', block),
    ]
    prepared = []
    for path, anchor, addition in changes:
        text = path.read_text()
        if 'APP_EOIP' in text or '"eoip_enable"' in text or '"eoip_slot' in text:
            raise SystemExit(f'EoIP defaults already present: {path}')
        if text.count(anchor) != 1:
            raise SystemExit(f'EoIP defaults anchor changed: {path}')
        prepared.append((path, text.replace(anchor, addition + anchor)))
    path = user / 'rc/services.c'
    text = path.read_text()
    if 'APP_EOIP' in text:
        raise SystemExit(f'EoIP lifecycle already present: {path}')
    for anchor, action in [('\tstart_iperf3();\n#endif\n', 'boot'),
                           ('\tstop_iperf3();\n#endif\n', 'stop')]:
        if text.count(anchor) != 1:
            raise SystemExit(f'EoIP lifecycle anchor changed: {path}')
        addition = ('#if defined(APP_EOIP)\n'
                    f'\tif (eval("/usr/bin/wr-eoip-boot", "{action}") != 0)\n'
                    '\t\tlogmessage("EoIP", "Lifecycle action incomplete; inspect slot status");\n'
                    '#endif\n')
        text = text.replace(anchor, anchor + addition)
    prepared.append((path, text))
    # A dedicated rc notification needs no General Apply event bit and avoids
    # coupling EoIP to restart_vpn or another unrelated service transaction.
    path = user / 'shared/notify_rc.h'
    text = path.read_text()
    lines = text.splitlines(keepends=True)
    matches = [i for i, line in enumerate(lines)
               if line.split(maxsplit=2)[:2] == ['#define', 'RCN_RESTART_IPERF3']]
    if len(matches) != 1 or 'RCN_APPLY_EOIP' in text:
        raise SystemExit(f'EoIP notification declaration anchor changed: {path}')
    lines.insert(matches[0], '#define RCN_APPLY_EOIP "apply_eoip"\n')
    prepared.append((path, ''.join(lines)))
    path = user / 'rc/rc.c'
    text = path.read_text()
    anchor = '#if defined(APP_IPERF3)\n\t\telse if (strcmp(entry->d_name, RCN_RESTART_IPERF3) == 0)'
    if text.count(anchor) != 1 or 'RCN_APPLY_EOIP' in text:
        raise SystemExit(f'EoIP notification handler anchor changed: {path}')
    addition = ('#if defined(APP_EOIP)\n'
                '\t\telse if (strcmp(entry->d_name, RCN_APPLY_EOIP) == 0)\n'
                '\t\t{\n'
                '\t\t\tif (eval("/usr/bin/wr-eoip-boot", "apply") != 0)\n'
                '\t\t\t\tlogmessage("EoIP", "Apply incomplete; inspect observed slot state");\n'
                '\t\t}\n#endif\n')
    prepared.append((path, text.replace(anchor, addition + anchor)))
    for path, text in prepared:
        path.write_text(text)
    print('Prepared disabled EoIP master and eight persistent slot defaults')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    parser.add_argument('--config', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.source, args.config)
