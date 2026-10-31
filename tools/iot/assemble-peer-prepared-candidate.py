#!/usr/bin/env python3
"""Merge the reviewed scheduler82 tree with prepared steering/RSSI sources.

An isolated source candidate only. No production installation or target proof.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

CONFLICT = re.compile(r'^<<<<<<< [^\n]*\n(.*?)^=======\n(.*?)^>>>>>>> [^\n]*\n', re.M | re.S)
PINS = {
    'common/rtmp_init.c': (
        'e5f8f087f2184abbcf1cc3424d3103f1b41e59ffc8525dc5c37e1392e29e23a1',
        'cb0078af9f9cd064b2e4ed2a27a33b99ea78e357d7dae5391bf7b1d916cd443b'),
    'include/rtmp.h': (
        '3ffbde3016682e0e604e00e9ec676afe88ecf1ed93200a9ddba19d844ebe5cda',
        '27641008d8a74922ca1c81fe28caaf3f4e29dbb106c694c9d76b2a28f54082e0'),
    'mgmt/mgmt_entrytb.c': (
        '4e8ed663c91ab6d0995a6daedee6309f3ac5a5ede337fe2e2d360de95222d88c',
        'cef37395a9649dce3c1937915c156b7a0d7574aca24df47fb6fed918201dd58b'),
}
OVERLAPS = set(PINS) | {'ap/ap.c', 'ap/ap_cfg.c', 'hw_ctrl/cmm_asic_mt.c'}
# Production station-query bounds are an additional, separately reviewed merge.
PRODUCTION_PINS = {
    'common/cmm_info.c': (
        '7f08d80fc1582e0cfff1da1b9f5448049df5d4852908b69047a27149264d016c',
        '919be03073f34bb8c62b7b662f85399f35d626dcd82bfd5be5e5b4e0c834e11a',
        'fd93f73da2e93655cb420aed54fdd9cdf41eeecefdb73447436301b59451bbdb'),
}

BODY = ('static BOOLEAN wr_iot_mac_delete_entry_body(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr,\n'
        ' const void *wr_resume_device, unsigned long wr_resume_generation, unsigned long wr_resume_serial, unsigned long wr_table_serial)')
RSSI = ('BOOLEAN wr_rssi_delete_entry(RTMP_ADAPTER *pAd, USHORT wcid, UCHAR *pAddr, '
        'const struct wr_rssi_identity *identity, const struct wr_rssi_record *attempt)')
CONTEXT = ',const struct wr_rssi_identity *identity,const struct wr_rssi_record *attempt'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory(root):
    result = {}
    for path in root.rglob('*'):
        if path.is_symlink():
            raise ValueError('Symlink input refused: ' + str(path))
        if path.is_file():
            result[path.relative_to(root).as_posix()] = path.read_bytes()
    return result


def norm(data):
    return data.replace(b'\r\n', b'\n')


def once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Changed RSSI/deletion integration anchor: ' + old[:80])
    return text.replace(old, new, 1)


def deletion_context(table, lease):
    # Undo the misleading automatic merge of the two function renames. Keep
    # both contexts inside one body, reached only through the execution lease.
    stub = BODY + '\n{\n    return wr_rssi_delete_entry(pAd, wcid, pAddr, NULL, NULL);\n}\n\n' + RSSI
    table = once(table, stub, BODY[:-1] + CONTEXT + ')')
    expected = Path(__file__).with_name('peer-delete-execution.inc').read_text(encoding='utf-8')
    if lease != expected:
        raise ValueError('Unreviewed deletion execution lease')
    signature = ('static BOOLEAN wr_iot_mac_delete_entry(RTMP_ADAPTER *pAd,USHORT wcid,UCHAR *pAddr,\n'
                 ' const void *device,unsigned long generation,unsigned long resume_serial,unsigned long table_serial)')
    lease = once(lease, signature, signature[:-1].replace(
        'wr_iot_mac_delete_entry(', 'wr_iot_mac_delete_entry_observed(') + CONTEXT + ')')
    lease = once(lease,
        'wr_iot_mac_delete_entry_body(pAd,wcid,pAddr,device,generation,resume_serial,table_serial);',
        'wr_iot_mac_delete_entry_body(pAd,wcid,pAddr,device,generation,resume_serial,table_serial,identity,attempt);')
    lease += '\n' + signature + '''
{
 return wr_iot_mac_delete_entry_observed(pAd,wcid,pAddr,device,generation,resume_serial,table_serial,NULL,NULL);
}
''' + RSSI + '''
{
 return wr_iot_mac_delete_entry_observed(pAd,wcid,pAddr,NULL,0,0,0,identity,attempt);
}
'''
    if table.count(BODY[:-1] + CONTEXT + ')') != 1 or RSSI in table:
        raise ValueError('Deletion body was not uniquely integrated')
    return table, lease


def merge(name, base, prepared, candidate):
    with tempfile.TemporaryDirectory(prefix='wr-iot-peer-merge-') as directory:
        paths = []
        for label, data in [('prepared', prepared), ('base', base), ('candidate', candidate)]:
            path = Path(directory) / label
            path.write_bytes(norm(data))
            paths.append(str(path))
        result = subprocess.run(['git', 'merge-file', '-p', *paths], capture_output=True)
    if result.returncode not in (0, 1):
        raise ValueError('merge-file failed for ' + name)
    text = result.stdout.decode('utf-8')
    conflicts = list(CONFLICT.finditer(text))
    if name in PINS:
        if result.returncode != 1 or len(conflicts) != 1:
            raise ValueError('Expected one reviewed conflict in ' + name)
        section = conflicts[0]
        hashes = tuple(sha(section.group(i).strip().encode()) for i in (1, 2))
        if hashes != PINS[name]:
            raise ValueError('Unreviewed conflict in ' + name)
        text = text[:section.start()] + section.group(1) + section.group(2) + text[section.end():]
    elif result.returncode or conflicts:
        raise ValueError('Unexpected conflict in ' + name)
    if '<<<<<<< ' in text:
        raise ValueError('Unresolved merge marker in ' + name)
    if name in PRODUCTION_PINS:
        observed = (sha(norm(prepared)), sha(norm(candidate)), sha(text.encode()))
        if observed != PRODUCTION_PINS[name]:
            raise ValueError('Unreviewed production merge in ' + name)
    return text.encode()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('pinned_driver', type=Path)
    p.add_argument('prepared_driver', type=Path)
    p.add_argument('peer_receipt', type=Path)
    p.add_argument('base_receipt', type=Path, help='Full-overlay receipt with base_sha256')
    p.add_argument('output', type=Path)
    a = p.parse_args()
    receipt = json.loads(a.peer_receipt.read_text(encoding='utf-8'))
    candidate_root = Path(receipt['candidate']).resolve(strict=True)
    roots = [a.pinned_driver.resolve(strict=True), a.prepared_driver.resolve(strict=True), candidate_root]
    output = a.output.resolve()
    if output.exists() or output.with_name(output.name + '.manifest.json').exists() or any(
            output == r or output in r.parents or r in output.parents for r in roots):
        p.error('New separate output and manifest required')
    try:
        base, prepared, candidate = map(inventory, roots)
        provenance = json.loads(a.base_receipt.read_text(encoding='utf-8'))
        if provenance.get('source_revision') != 'c25283e915a2a00a763774dd255b14aff997285e' or {
                n: sha(b) for n, b in base.items()} != provenance['base_sha256']:
            raise ValueError('Pinned base receipt mismatch')
        if any(receipt.get(k) is not False for k in ('target_compiled', 'production_installed', 'runtime_verified')):
            raise ValueError('Unexpected candidate acceptance claims')
        if {n: sha(b) for n, b in candidate.items()} != receipt['files']:
            raise ValueError('Peer candidate differs from receipt')
        if receipt.get('asset_policy_sha256') != sha(Path(__file__).with_name('candidate_assets.py').read_bytes()):
            raise ValueError('Candidate asset policy differs from receipt')
        stages = receipt['stages']
        if len(stages) != 74 or stages[-1]['stage'] != 'aux-family-retry-scheduler':
            raise ValueError('Unreviewed peer chain variant')
        for stage in stages:
            script = stage['script']
            if Path(script).name != script or sha(Path(__file__).with_name(script).read_bytes()) != stage['script_sha256']:
                raise ValueError('Peer generator changed: ' + script)
        if base.keys() - candidate.keys():
            raise ValueError('Candidate dropped original source files')
        changed = {n for n in base if norm(base[n]) != norm(candidate[n])}
        added = candidate.keys() - base.keys()
        if (len(changed), len(added), len(candidate)) != (62, 70, 585):
            raise ValueError('Unreviewed scheduler82 inventory')
        overlaps = {n for n in changed if n in prepared and norm(prepared[n]) != norm(base[n])}
        missing = base.keys() - prepared.keys()
        collisions = added & prepared.keys()
        if overlaps not in (OVERLAPS, OVERLAPS | set(PRODUCTION_PINS)) or missing or collisions:
            raise ValueError('Prepared source overlap/inventory changed: overlaps=' +
                             repr(sorted(overlaps)) + '; missing=' + repr(sorted(missing)) +
                             '; collisions=' + repr(sorted(collisions)))
        payloads = {n: norm(candidate[n]) for n in changed | added}
        for name in sorted(overlaps):
            payloads[name] = merge(name, base[name], prepared[name], candidate[name])
        name = 'mgmt/mgmt_entrytb.c'
        lease = 'include/wr-iot-peer-normal-delete.inc'
        table, execution = deletion_context(payloads[name].decode(), payloads[lease].decode())
        payloads[name], payloads[lease] = table.encode(), execution.encode()
        # Vendor probe deliberately stores the adapter as void *. The staged
        # work-join calls must use its concrete type, as the remove path does.
        name = 'os/linux/pci_main_dev.c'
        probe = payloads[name].decode()
        if probe.count('void *pAd = NULL, *handle;') != 1:
            raise ValueError('Changed vendor PCI probe adapter declaration')
        for member in ('wr_iot_main_recovery_reap_work', 'wr_iot_main_recovery_work',
                       'wr_iot_aux_family_retry_work'):
            probe = once(probe, '&pAd->' + member, '&((PRTMP_ADAPTER)pAd)->' + member)
        payloads[name] = probe.encode()
        # All validation and conflict handling precede output creation.
        shutil.copytree(roots[1], output)
        for name, data in payloads.items():
            path = output / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        actual = inventory(output)
        expected = dict(prepared)
        expected.update(payloads)
        if actual != expected:
            raise ValueError('Merged output byte verification failed')
        report = {'source_revision': provenance['source_revision'],
                  'overlay_count': len(payloads), 'prepared_overlaps': sorted(overlaps),
                  'resolved_conflicts': sorted(PINS), 'rssi_delete_lease_integrated': True,
                  'typed_pci_probe_work_join': True,
                  'input_peer_sha256': receipt['files'],
                  'candidate_driver_sha256': {n: sha(actual[n]) for n in payloads},
                  'merged_driver_sha256': {n: sha(b) for n, b in actual.items()},
                  'target_compiled': False, 'production_installed': False, 'runtime_verified': False}
        output.with_name(output.name + '.manifest.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    except (ValueError, KeyError, OSError) as error:
        p.error(str(error))
    print('PASS isolated scheduler82/RSSI source merge; target and runtime unverified')


if __name__ == '__main__':
    main()
