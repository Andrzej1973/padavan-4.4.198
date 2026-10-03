#!/usr/bin/env python3
"""Compare requested firmware policy with the effective WR1200JS config."""
import argparse
import json
import re
from pathlib import Path


def read_config(path):
    values = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        match = re.fullmatch(r'(CONFIG_[A-Za-z0-9_]+)=(.*)', line.strip())
        disabled = re.fullmatch(r'#\s*(CONFIG_[A-Za-z0-9_]+)(?:=.*| is not set)', line.strip())
        if match:
            key, value = match.groups()
        elif disabled:
            key, value = disabled.group(1), 'n'
        else:
            continue
        if key in values and values[key] != value:
            raise ValueError('Conflicting configuration entries: ' + key)
        values[key] = value
    return values


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('requested', type=Path)
    parser.add_argument('effective', type=Path)
    parser.add_argument('kernel', type=Path)
    parser.add_argument('--report', required=True, type=Path)
    args = parser.parse_args()
    requested = read_config(args.requested)
    effective = read_config(args.effective)
    kernel = read_config(args.kernel)
    rows, errors = [], []
    aliases = {'CONFIG_FIRMWARE_INCLUDE_SHORTCUT_FE': 'CONFIG_FIRMWARE_INCLUDE_SFE'}
    modes = ('CONFIG_FIRMWARE_INCLUDE_SSREDIR', 'CONFIG_FIRMWARE_INCLUDE_SSLOCAL')
    for key, value in sorted(requested.items()):
        if not key.startswith('CONFIG_FIRMWARE_'):
            continue
        row = {'requested_key': key, 'requested_value': value}
        if key == 'CONFIG_FIRMWARE_CPU_SLEEP' and value == 'y':
            row.update(status='port_pending', reason='Only an isolated systick kernel candidate has linked; the main image does not implement this selector.')
            rows.append(row)
            continue
        if key in ('CONFIG_FIRMWARE_WIFI2_DRIVER', 'CONFIG_FIRMWARE_WIFI5_DRIVER'):
            symbol, supported = (('CONFIG_FIRST_IF_MT7603E', '4.1') if key.endswith('WIFI2_DRIVER')
                                 else ('CONFIG_RT_SECOND_IF_MT7612E', '3.0'))
            valid = value == supported and kernel.get(symbol) == 'y'
            row.update(status='kernel_selection_verified' if valid else 'mismatch',
                       kernel_key=symbol, kernel_value=kernel.get(symbol),
                       note='Checks driver family selection, not source revision or runtime calibration.')
            if not valid:
                errors.append(key)
            rows.append(row)
            continue
        mapped = aliases.get(key, key)
        expected = value
        if key in modes:
            mapped = 'CONFIG_FIRMWARE_INCLUDE_SHADOWSOCKS'
            expected = 'y' if any(requested.get(mode) == 'y' for mode in modes) else 'n'
        actual = effective.get(mapped)
        # A disabled absent selector does not enable a package. Enabled requests
        # must exist in the prepared target, including newly added port selectors.
        valid = actual == expected or (expected == 'n' and actual is None)
        row.update(effective_key=mapped, effective_value=actual,
                   expected_effective_value=expected,
                   status='config_verified' if valid else 'mismatch')
        if not valid:
            errors.append(key)
        rows.append(row)
    for key, expected in [('CONFIG_VENDOR', 'Ralink'), ('CONFIG_PRODUCT', 'MT7621')]:
        if effective.get(key) != expected:
            errors.append(key)
    if kernel.get('CONFIG_RALINK_BUILTIN_DTB_NAME') != '"wr1200js"':
        errors.append('CONFIG_RALINK_BUILTIN_DTB_NAME')
    report = {'board': 'wr1200js', 'scope': 'Requested versus effective configuration; not package, runtime or complete-port proof',
              'mismatches': errors, 'options': rows,
              'pending_options': [row['requested_key'] for row in rows if row['status'] == 'port_pending']}
    args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if errors:
        raise SystemExit('Requested configuration mismatch: ' + ', '.join(errors))
    print('WR1200JS config policy checked; pending options: ' + ', '.join(report['pending_options']))


if __name__ == '__main__':
    main()
