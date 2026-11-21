#!/usr/bin/env python3
"""Replay relevant actual generator fragments into the experimental composer.

The input contains the relevant source slices and helpers. Full prepared driver
and target Kbuild verification remain separate requirements.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import tarfile
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive', type=Path, required=True)
args = parser.parse_args()
here = Path(__file__).resolve().parent
legacy = runpy.run_path(str(here / 'check-tracked-beacon-reservation.py'))
with tempfile.TemporaryDirectory(prefix='wr-ra2-bundle-compose-') as scratch:
    root = Path(scratch)
    lower = legacy['predecessor'](root, args.archive)
    source = root / 'bundle/driver'
    (source / 'common/cmm_mac_pci.c').write_text(legacy['POLICY']['compose'](lower))
    pinned = root / 'pinned'
    checked = root / 'checked'
    with tarfile.open(args.archive) as archive:
        for name in runpy.run_path(str(here / 'prepare-txs-status-candidate.py'))['PINNED_BLOBS']:
            path = pinned / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(archive.extractfile('trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/' + name).read())
    subprocess.run(['python3', '-B', str(here / 'prepare-txs-status-candidate.py'), str(pinned), str(checked)], check=True, stdout=subprocess.DEVNULL)
    for name in ('mac/mt_mac.c', 'tx_rx/txs.c'):
        path = source / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes((checked / name).read_bytes())
    producer = ast.parse((here / 'prepare-beacon-producer-candidate.py').read_text())
    wrapper = next(ast.literal_eval(node.value) for node in ast.walk(producer)
                   if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'beacon_wrapper' for t in node.targets))
    environment = {'beacon_wrapper': wrapper}
    connect = (source / 'ap/ap_connect.c').read_text()
    for node in ast.walk(producer):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'edit'
                and isinstance(node.args[1], ast.Constant) and node.args[1].value == 'ap/ap_connect.c'):
            edits = eval(compile(ast.Expression(node.args[2]), 'actual-producer-edits', 'eval'), environment)
            for old, new, label in edits:
                assert connect.count(old) == 1, label
                connect = connect.replace(old, new, 1)
    header = (here / 'beacon-producer-kernel.h').read_text()
    api = ast.parse((here / 'prepare-driver-api.py').read_text())
    for node in api.body:
        if not isinstance(node, ast.Expr) or not isinstance(node.value, ast.Call):
            continue
        call = node.value
        if not isinstance(call.func, ast.Name) or call.func.id != 'one' or not isinstance(call.args[0], ast.Constant):
            continue
        name = call.args[0].value
        if name == 'include/wr-iot-beacon-producer-kernel.h':
            old, new = map(ast.literal_eval, call.args[1:])
            assert header.count(old) == 1
            header = header.replace(old, new, 1)
        elif name == 'ap/ap_connect.c':
            old, new = map(ast.literal_eval, call.args[1:])
            if 'wr_iot_APUpdateBeaconFrame_inner' in old:
                assert connect.count(old) == 1
                connect = connect.replace(old, new, 1)
    (source / 'ap/ap_connect.c').write_text(connect)
    (source / 'include/wr-iot-beacon-producer-kernel.h').write_text(header)
    (source / 'include/wr-iot-beacon-producer-gate.h').write_bytes((here / 'beacon-producer-gate.h').read_bytes())
    (source / 'include/driver-api-closed-entry.inc').write_bytes((here / 'driver-api-closed-entry.inc').read_bytes())
    # Reproduce the actual API storage/init and retirement predecessor layers.
    rtmp = (source / 'include/rtmp.h').read_text()
    rtmp += '\n#include "mbss-closed-probe.h"\n struct wr_iot_mbss_closed_probe wr_iot_closed_probe;\n'
    (source / 'include/rtmp.h').write_text(rtmp)
    (source / 'common/rtmp_init.c').write_text('NdisZeroMemory(&pAd->wr_iot_closed_probe,sizeof(pAd->wr_iot_closed_probe));\n')
    owners = runpy.run_path(str(here / 'close-owner-composition.py'))
    work = owners['compose_recovery_idle']((here / 'mbss-recovery-work.inc').read_text())
    join = (here / 'mbss-recovery-join.inc').read_text()
    tree = ast.parse((here / 'prepare-mbss-reaper-gate.py').read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == 'one' and len(node.args) == 3:
            if isinstance(node.args[1], ast.Constant) and node.args[1].value == ' ready=wr_iot_mbss_recovery_idle_locked(ad);':
                old, new = map(ast.literal_eval, node.args[1:]); assert join.count(old) == 1; join = join.replace(old, new)
    join = owners['compose_recovery_join'](join)
    (source / 'include/wr-iot-mbss-recovery-work.inc').write_text(work)
    (source / 'include/wr-iot-mbss-recovery-join.inc').write_text(join)
    hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in source.rglob('*') if p.is_file()}
    manifest = {'production_installed': False, 'target_compiled': False,
                'linux_open_api': {}, 'merged_driver_sha256': hashes, 'candidate_driver_sha256': hashes}
    Path(str(source) + '.manifest.json').write_text(json.dumps(manifest))
    output = root / 'experiment'
    subprocess.run(['python3', '-B', str(here / 'prepare-ra2-no-host-experiment.py'), str(source), str(output)], check=True)
    # Every MT virtual beacon builder call must remain behind the periodic
    # predicate. Otherwise a count mismatch could reach the tracked allocator
    # before lower submission rejects the experimental packet.
    connect_output = (output / 'ap/ap_connect.c').read_text()
    wrapper_start = connect_output.index('VOID APUpdateBeaconFrame(RTMP_ADAPTER *pAd, INT apidx)')
    wrapper_end = connect_output.index('\n}', wrapper_start) + 2
    wrapper_output = connect_output[wrapper_start:wrapper_end]
    guarded_call = ('  if (wr_iot_bcn_periodic_ready(pAd, apidx, &ticket))\n'
                    '   wr_iot_APUpdateBeaconFrame_inner(pAd, apidx, &ticket);')
    assert wrapper_output.count(guarded_call) == 1
    assert wrapper_output.index('wr_iot_bcn_producer_begin(') < wrapper_output.index(guarded_call)
    assert wrapper_output.index(guarded_call) < wrapper_output.index('wr_iot_bcn_producer_end(')
    periodic_output = (output / 'include/wr-iot-beacon-producer-kernel.h').read_text()
    assert 'ready=ad->ApCfg.BssidNum==3&&' in periodic_output
    result = json.loads(Path(str(output) + '.manifest.json').read_text())
    actual = {str(p.relative_to(output)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in output.rglob('*') if p.is_file()}
    assert result['merged_driver_sha256'] == actual == result['candidate_driver_sha256']
    assert len(result['ra2_no_host_experiment']['changed_paths']) == 24
    assert result['ra2_no_host_experiment']['activation_ready'] is False
    for name in result['ra2_no_host_experiment']['changed_paths']:
        assert '#include "beacon-producer-gate.h"' not in (output / name).read_text()
    assert (output / 'include/wr-iot-beacon-producer-gate.h').read_bytes() == (here / 'beacon-producer-gate.h').read_bytes()
    assert hashes == {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                      for p in source.rglob('*') if p.is_file()}
    helper_path = source / 'ap/ap_connect.c'
    original_helper = helper_path.read_text()
    helper_path.write_text(original_helper.replace('mac_info.TxSPriv = apidx;',
                                                  'mac_info.TxSPriv = apidx; mac_info.PID = 7;', 1))
    drift_hashes = {str(p.relative_to(source)): hashlib.sha256(p.read_bytes()).hexdigest()
                    for p in source.rglob('*') if p.is_file()}
    manifest['merged_driver_sha256'] = manifest['candidate_driver_sha256'] = drift_hashes
    Path(str(source) + '.manifest.json').write_text(json.dumps(manifest))
    refused_output = root / 'refused-pid'
    refused = subprocess.run(['python3', '-B', str(here / 'prepare-ra2-no-host-experiment.py'),
                              str(source), str(refused_output)], capture_output=True, text=True)
    assert refused.returncode and 'zero-PID contract changed' in refused.stderr
    assert not refused_output.exists()
    print('PASS twenty-four-path source composition from actual generator fragments, output hashes and input preservation. Full driver/Kbuild verification pending.')
