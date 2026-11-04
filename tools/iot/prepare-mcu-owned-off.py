#!/usr/bin/env python3
"""Bind the isolated checked radio OFF to a serial-owned sender drain."""
import argparse
import hashlib
import json
from pathlib import Path


def prepare(files):
    changes = dict(files)
    def one(name, old, new):
        if changes[name].count(old) != 1:
            raise ValueError('Unexpected owned OFF anchor: ' + name + ': ' + old)
        changes[name] = changes[name].replace(old, new)
    old = 'INT32 wr_iot_send_radio_off_checked(RTMP_ADAPTER *pAd)'
    new = old[:-1] + ', const struct wr_iot_radio_ticket *ticket)'
    one('mcu/andes_mt.c', old, new)
    # Restrict replacement to this function: generic senders remain unchanged.
    text = changes['mcu/andes_mt.c']; start = text.index(new)
    end = text.index('\n}', start)
    body = text[start:end]
    if body.count('return AndesSendCmdMsg(pAd,msg);') != 1:
        raise ValueError('Unexpected checked OFF transport')
    changes['mcu/andes_mt.c'] = (text[:start] + body.replace(
        'return AndesSendCmdMsg(pAd,msg);',
        'return wr_iot_mcu_send_owned_off(pAd,msg,ticket);') + text[end:])
    one('include/rtmp.h', old + ';', new + ';\nstruct cmd_msg;\n'
        'INT32 wr_iot_mcu_send_owned_off(RTMP_ADAPTER *ad,struct cmd_msg *msg,\n'
        ' const struct wr_iot_radio_ticket *ticket);')
    one('hw_ctrl/cmm_asic_mt.c', 'wr_iot_send_radio_off_checked(pAd)',
        'wr_iot_send_radio_off_checked(pAd,ticket)')
    one('mcu/andes_core.c', '#include "wr-iot-mcu-sender-drain.inc"',
        '#include "wr-iot-mcu-sender-drain.inc"\n#include "wr-iot-mcu-owned-off.inc"')
    return changes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('driver', type=Path)
    args = parser.parse_args(); root = args.driver
    manifest_path = root.with_name(root.name + '.manifest.json')
    manifest = json.loads(manifest_path.read_text())
    actual = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in root.rglob('*') if p.is_file()}
    if (manifest.get('production_installed') is not False or
        manifest.get('target_compiled') is not False or
        actual != manifest['merged_driver_sha256']):
        parser.error('Expected unchanged isolated candidate')
    names = ('mcu/andes_mt.c','mcu/andes_core.c','include/rtmp.h','hw_ctrl/cmm_asic_mt.c')
    changes = prepare({name: (root/name).read_text() for name in names})
    asset = 'include/wr-iot-mcu-owned-off.inc'
    if (root/asset).exists(): parser.error('Owned OFF already present')
    changes[asset] = Path(__file__).with_name('mcu-owned-off.inc').read_text()
    for name, text in changes.items():
        (root/name).write_text(text)
        digest = hashlib.sha256((root/name).read_bytes()).hexdigest()
        manifest['merged_driver_sha256'][name] = digest
        manifest['candidate_driver_sha256'][name] = digest
    manifest['mcu_owned_off'] = {'target_compiled':False,'runtime_verified':False,
                               'firmware_epoch_verified':False}
    manifest_path.write_text(json.dumps(manifest,indent=2)+'\n')


if __name__ == '__main__':
    main()
