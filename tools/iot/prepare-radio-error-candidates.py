#!/usr/bin/env python3
"""Assemble reviewed radio-error candidates outside the source tree.

This is a partial source bundle, not a firmware/driver installer. No board
profile, BSSID count, radio state or production build path is changed.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('source', type=Path, help='mt76x3 driver source directory')
p.add_argument('output', type=Path, help='new, separate candidate directory')
a = p.parse_args()
root = a.source.resolve()
out = a.output.resolve()
if out == root or root in out.parents or out in root.parents or a.output.exists():
    raise SystemExit('Output must be a new directory separate from the source tree')
entries = (
    ('ap/ap_mbss.c', '92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f', 'prepare-mbss-init-check.py', 'mbss-init'),
    ('ap/ap_mbss_inf.c', '7c736a04eeeddace0bbb0c5c96198d0738f400a2', 'prepare-mbss-open-check.py', 'mbss-open'),
    ('os/linux/rt_linux.c', 'db61215d188d82a50f3468747fff871318fc4b72', 'prepare-netdev-create-check.py', 'netdev-create'),
    ('ap/ap_connect.c', '0c7565b84fb202e9a71c1669b4d1ed219ad229eb', 'prepare-beacon-guard-check.py', 'beacon-guard'),
    ('hw_ctrl/cmm_asic_mt.c', 'a8c0c0ec59c7e51c88296111934597064cf36c4a', 'prepare-dma-idle-check.py', 'dma-idle'),
    ('common/cmm_mac_pci.c', '82db49fa1822a51268d76f23bce94d886f4d50d6', 'prepare-beacon-kickout-check.py', 'beacon-kickout'),
)
support_blobs = {
    'ap/ap_cfg.c': '17853ec17d577021ce876c5ec6d8909e27a7453b',
    'include/rtmp_cmd.h': 'adfd19a69fac4fa3b08ca113f7a88b9016e25a67',
    'include/ap_mbss.h': '667b4728f1ade6f7030b2c23ef24cc413617ff3b',
}
audit_blobs = {
    'ate/mt_mac/mt_ate.c': 'd8ed09f71cdb82746479d1d9ac1bb120154682ad',
}
def git_blob(data):
    return hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()

# Check every original before creating anything. Drift is a review request,
# never permission to replace locally modified source with upstream bytes.
originals = {}
for name, expected, _, _ in entries:
    data = (root / name).read_bytes()
    if git_blob(data) != expected:
        raise SystemExit('Unreviewed source bytes: ' + name)
    originals[name] = data
for name, expected in support_blobs.items():
    data = (root / name).read_bytes()
    if git_blob(data) != expected:
        raise SystemExit('Unreviewed support source bytes: ' + name)
    originals[name] = data
for name, expected in audit_blobs.items():
    data = (root / name).read_bytes()
    if git_blob(data) != expected:
        raise SystemExit('Unreviewed flag-writer source bytes: ' + name)
    originals[name] = data

flag_pattern = re.compile(
    r'RTMP_(SET|CLEAR)_FLAG\s*\(\s*pAd\s*,\s*'
    r'fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET\s*\)')
expected_flag_writers = {
    'ate/mt_mac/mt_ate.c': ['SET', 'SET', 'CLEAR', 'SET', 'CLEAR'],
    'common/cmm_mac_pci.c': ['SET', 'CLEAR'],
    'hw_ctrl/cmm_asic_mt.c': ['CLEAR', 'SET'],
}
flag_writers = {}
for path in root.rglob('*.c'):
    operations = flag_pattern.findall(path.read_bytes().decode('utf-8', errors='ignore'))
    if operations:
        flag_writers[path.relative_to(root).as_posix()] = operations
if flag_writers != expected_flag_writers:
    raise SystemExit('Unreviewed dequeue-disable flag writers')
out.mkdir(parents=False)
records = []
for name, expected, generator, fixture in entries:
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    check = out / (fixture + '-check.c')
    additional = []
    if name == 'ap/ap_mbss.c':
        lifecycle = out / 'mbss-lifecycle'
        subprocess.run([sys.executable, str(Path(__file__).with_name('prepare-mbss-lifecycle-candidate.py')),
                        str(root / name), str(lifecycle)], check=True)
        target.write_bytes((lifecycle / 'ap/ap_mbss.c').read_bytes())
        check.write_bytes((lifecycle / 'check-init.c').read_bytes())
        for group in ('open-state', 'close', 'cr'):
            extra = out / ('mbss-' + group + '-check.c')
            extra.write_bytes((lifecycle / ('check-' + group + '.c')).read_bytes())
            additional.append(extra.name)
    else:
        subprocess.run([sys.executable, str(Path(__file__).with_name(generator)),
                        str(root / name), str(target), str(check)], check=True)
    if name == 'hw_ctrl/cmm_asic_mt.c':
        recovery = out / 'beacon-recovery-candidate.c'
        extra = out / 'beacon-recovery-check.c'
        subprocess.run([sys.executable, str(Path(__file__).with_name('prepare-beacon-recovery-check.py')),
                        str(root / name), str(recovery), str(extra)], check=True)
        signature = 'VOID APCheckBcnQHandler(RTMP_ADAPTER *pAd, INT apidx, BOOLEAN *is_pretbtt_int)'
        def recovery_function(text):
            if text.count(signature) != 1:
                raise SystemExit('Changed beacon recovery function')
            start = text.index(signature)
            return text[start:text.index('\n}', start) + 2]
        original = originals[name].decode('utf-8')
        candidate = recovery.read_text(encoding='utf-8')
        old, new = recovery_function(original), recovery_function(candidate)
        if candidate.replace(new, old, 1) != original:
            raise SystemExit('Unexpected beacon recovery edits')
        merged = target.read_text(encoding='utf-8')
        if merged.count(old) != 1:
            raise SystemExit('DMA/beacon candidate conflict')
        target.write_text(merged.replace(old, new, 1), encoding='utf-8')
        additional.append(extra.name)
        sync_candidate = out / 'bss-sync-candidate.c'
        sync_check = out / 'bss-sync-check.c'
        subprocess.run([sys.executable, str(Path(__file__).with_name('prepare-bss-sync-lock-check.py')),
                        str(root / name), str(sync_candidate), str(sync_check)], check=True)
        sync_text = sync_candidate.read_text(encoding='utf-8')
        signatures = ('VOID AsicEnableBssSync(RTMP_ADAPTER *pAd, USHORT BeaconPeriod)',
                      'VOID AsicEnableApBssSync(RTMP_ADAPTER *pAd, USHORT BeaconPeriod)')
        restored = sync_text
        merged = target.read_text(encoding='utf-8')
        for sig in signatures:
            def selected(text):
                if text.count(sig) != 1:
                    raise SystemExit('Changed BSS sync function: ' + sig)
                start = text.index(sig)
                return text[start:text.index('\n}', start) + 2]
            previous, replacement = selected(original), selected(sync_text)
            restored = restored.replace(replacement, previous, 1)
            if merged.count(previous) != 1:
                raise SystemExit('BSS sync candidate conflict: ' + sig)
            merged = merged.replace(previous, replacement, 1)
        if restored != original:
            raise SystemExit('Unexpected BSS sync edits')
        target.write_text(merged, encoding='utf-8')
        additional.append(sync_check.name)
    if name == 'common/cmm_mac_pci.c':
        reset_candidate = out / 'pdma-reset-gate-candidate.c'
        reset_check = out / 'pdma-reset-gate-check.c'
        subprocess.run([sys.executable, str(Path(__file__).with_name('prepare-pdma-reset-gate-check.py')),
                        str(root / name), str(reset_candidate), str(reset_check)], check=True)
        signature = 'VOID PDMAResetAndRecovery(RTMP_ADAPTER *pAd)'
        def reset_function(text):
            if text.count(signature) != 1:
                raise SystemExit('Changed PDMA reset function')
            start = text.index(signature)
            return text[start:text.index('\n}', start) + 2]
        original = originals[name].decode('utf-8')
        reset_text = reset_candidate.read_text(encoding='utf-8')
        old, new = reset_function(original), reset_function(reset_text)
        if reset_text.replace(new, old, 1) != original:
            raise SystemExit('Unexpected PDMA reset edits')
        merged = target.read_text(encoding='utf-8')
        if merged.count(old) != 1:
            raise SystemExit('PDMA reset candidate conflict')
        target.write_text(merged.replace(old, new, 1), encoding='utf-8')
        additional.append(reset_check.name)
    if (root / name).read_bytes() != originals[name]:
        raise SystemExit('Source changed during preparation: ' + name)
    records.append({'path': name, 'original_git_blob': expected,
                    'candidate_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                    'fixture': check.name, 'additional_fixtures': additional})
for name, data in originals.items():
    if (root / name).read_bytes() != data:
        raise SystemExit('Source changed before manifest: ' + name)
abort_dir = out / 'mbss-abort-open'
subprocess.run([sys.executable, str(Path(__file__).with_name('prepare-mbss-abort-open-check.py')),
                str(root), str(abort_dir)], check=True)
def function(text, signature):
    if text.count(signature) != 1:
        raise SystemExit('Changed function: ' + signature)
    start = text.index(signature)
    return text[start:text.index('\n}', start) + 2]
mbss_file = out / 'ap/ap_mbss.c'
mbss_text = mbss_file.read_text(encoding='utf-8')
abort_mbss = (abort_dir / 'ap/ap_mbss.c').read_text(encoding='utf-8')
helper = function(abort_mbss, 'INT MBSS_AbortOpen(PNET_DEV pDev)')
anchor = '''/*
========================================================================
Routine Description:
    Close a virtual network interface.'''
if mbss_text.count(anchor) != 1 or mbss_text.count('INT MBSS_AbortOpen(PNET_DEV pDev)'):
    raise SystemExit('MBSS helper merge conflict')
mbss_file.write_text(mbss_text.replace(anchor, helper+'\n\n'+anchor, 1), encoding='utf-8')
wrapper_file = out / 'ap/ap_mbss_inf.c'
wrapper_text = wrapper_file.read_text(encoding='utf-8')
signature = 'INT MBSS_VirtualIF_Open(PNET_DEV pDev)'
old_wrapper = function(wrapper_text, signature)
new_wrapper = function((abort_dir / 'ap/ap_mbss_inf.c').read_text(encoding='utf-8'), signature)
wrapper_file.write_text(wrapper_text.replace(old_wrapper, new_wrapper, 1), encoding='utf-8')
for name, expected in support_blobs.items():
    target = out / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((abort_dir / name).read_bytes())
    records.append({'path': name, 'original_git_blob': expected,
                    'candidate_sha256': hashlib.sha256(target.read_bytes()).hexdigest(),
                    'fixture': None, 'additional_fixtures': []})
abort_check = out / 'mbss-abort-open-check.c'
abort_check.write_bytes((abort_dir / 'check.c').read_bytes())
for record in records:
    target = out / record['path']
    record['candidate_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
    if (root / record['path']).read_bytes() != originals[record['path']]:
        raise SystemExit('Source changed before final manifest: ' + record['path'])
report = {'scope': 'WR1200JS mt76x3 isolated error-path candidates',
          'partial_source_bundle': True, 'production_installed': False,
          'runtime_verified': False, 'target_compiled': False,
          'mcu_response_lifetime_proven': False,
          'rf_quiescence_proven': False,
          'bss_close_exclusion_proven': False,
          'dequeue_flag_writer_coverage_proven': False,
          'dequeue_flag_writers': flag_writers,
          'activation_controller_bound': False,
          'bss_allocation_strategy': None,
          'source_ref': 'c25283e915a2a00a763774dd255b14aff997285e',
          'files': records, 'additional_fixtures': [abort_check.name]}
(out / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
print('Prepared isolated radio candidates; source unchanged, no production installation')
