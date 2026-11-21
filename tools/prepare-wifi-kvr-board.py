#!/usr/bin/env python3
"""Transfer only the approved WR1200JS KVR selectors into the build tree."""
import argparse
import re
from pathlib import Path

OPTIONS = ('CONFIG_MT7603E_DOT11R_FT_SUPPORT',
           'CONFIG_MT7603E_DOT11K_RRM_SUPPORT', 'CONFIG_MT7603E_WNM_SUPPORT')


def transform(target, approved):
    for text in (target, approved):
        for required in ('CONFIG_FIRST_IF_MT7603E=y', 'CONFIG_MT7603E_RLT_AP_SUPPORT=m'):
            if text.splitlines().count(required) != 1:
                raise ValueError('WR1200JS radio selection changed: ' + required)
    result = target
    for key in OPTIONS:
        pattern = r'^(?:' + key + r'=[^\n]*|# ' + key + r' is not set)$'
        if approved.splitlines().count(key + '=y') != 1:
            raise ValueError('Approved KVR selector missing: ' + key)
        if len(re.findall(pattern, result, re.M)) != 1:
            raise ValueError('Ambiguous or absent build selector: ' + key)
        result = re.sub(pattern, key + '=y', result, flags=re.M)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    relative = 'trunk/configs/boards/WR1200JS/kernel-4.4.x.config'
    approved = Path(__file__).resolve().parent.parent / 'overlay/padavan-4.4' / relative
    target = args.source / relative
    result = transform(target.read_text(encoding='utf-8'), approved.read_text(encoding='utf-8'))
    target.write_bytes(result.encode('utf-8'))
    print('Prepared three WR1200JS KVR selectors in actual build tree; runtime remains unverified')
