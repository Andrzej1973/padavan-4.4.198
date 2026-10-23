#!/usr/bin/env python3
"""Exercise the IoT capacity probe with small synthetic Kbuild source trees."""
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import runpy
from collections import Counter
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / 'tools/iot/check-capacity.py'
COMPILER = (os.environ.get('CC')
            or shutil.which('cc')
            or shutil.which('gcc')
            or shutil.which('clang'))
if not COMPILER:
    raise SystemExit('A host C compiler is required for the capacity self-test')


def make_fixture(base, radio, ceiling, features=()):
    kernel = base / 'kernel'
    driver = kernel / 'drivers/net/wireless/mediatek' / radio
    chips = driver / 'chips'
    (driver / 'include').mkdir(parents=True)
    chips.mkdir(parents=True)
    (driver / 'include/rtmp_def.h').write_text(
        '#ifdef MBSS_SUPPORT\n'
        '#undef MAX_MBSSID_NUM\n'
        '#define MAX_MBSSID_NUM(__pAd) ((__pAd)->chipCap.BcnMaxNum)\n'
        '#else\n'
        '#define MAX_MBSSID_NUM(__pAd) 1\n'
        '#endif\n'
    )
    source_path = f'drivers/net/wireless/mediatek/{radio}/chips/probe.c'
    (kernel / source_path).write_text('int capacity_probe;\n')

    if radio == 'mt76x3':
        (chips / 'mt7603.c').write_text(
            'VOID mt7603_init() { mt_bcn_buf_init(pAd); }\n'
        )
        (chips / 'rtmp_chip.c').write_text(
            'VOID mt_bcn_buf_init() { BcnMaxHwNum = 16; BcnMaxNum = 16; }\n'
        )
        defines = ['-DMT7603', '-DMT_MAC']
    else:
        (chips / 'mt76x2.c').write_text(
            'VOID mt76x2_init() { rlt_bcn_buf_init(pAd); }\n'
        )
        (chips / 'rtmp_chip.c').write_text(
            'VOID rlt_bcn_buf_init() {\n'
            '#if defined(MT7601) || defined(MT76x2)\n'
            'BcnMaxHwNum = 8;\n'
            '#endif\n'
            '#ifdef APCLI_SUPPORT\n'
            'pChipCap->BcnMaxNum = (8 - MAX_MESH_NUM);\n'
            '#else\n'
            'pChipCap->BcnMaxNum = (pChipCap->BcnMaxHwNum - MAX_MESH_NUM);\n'
            '#endif\n'
            '}\n'
        )
        defines = ['-DMT76x2', '-DRLT_MAC', '-DMAX_MESH_NUM=0']

    command = [
        COMPILER, '-DMBSS_SUPPORT', f'-DHW_BEACON_MAX_NUM={ceiling}',
        *defines, *features, '-c', source_path,
    ]
    # Kbuild records shell commands in POSIX form. On Windows, keep drive
    # paths absolute while avoiding backslashes that POSIX shlex treats as
    # escape characters when the checker reads the synthetic .cmd file.
    command[0] = command[0].replace('\\', '/')
    (chips / '.rtmp_chip.o.cmd').write_text(
        'cmd_chips/rtmp_chip.o := ' + shlex.join(command) + '\n'
    )
    if radio == 'mt76x3':
        pci_source = f'drivers/net/wireless/mediatek/{radio}/common/cmm_mac_pci.c'
        (driver / 'common').mkdir()
        (kernel / pci_source).write_text(
            '#ifndef RESOURCE_PRE_ALLOC\n'
            'void pci_free_lock(void) { RTMP_SEM_LOCK(&pAd->BcnRingLock); }\n'
            '#endif\n'
            'void pci_cleanup_lock(void) { RTMP_IRQ_LOCK(&pAd->BcnRingLock, flags); }\n')
        pci_command = [*command[:-1], pci_source]
        (driver / 'common/.cmm_mac_pci.o.cmd').write_text(
            'cmd_common/cmm_mac_pci.o := ' + shlex.join(pci_command) + '\n'
        )
        ap_source = f'drivers/net/wireless/mediatek/{radio}/ap/ap.c'
        (driver / 'ap').mkdir()
        (kernel / ap_source).write_text(
            'void ap_lock(void) { RTMP_IRQ_LOCK(&pAd->BcnRingLock, flags); }\n')
        ap_command = [*command[:-1], ap_source]
        (driver / 'ap/.ap.o.cmd').write_text(
            'cmd_ap/ap.o := ' + shlex.join(ap_command) + '\n'
        )
        (driver / 'ap/ap_cfg.c').write_text(
            '#ifdef DBG\n'
            'void cfg_lock(void) { RTMP_SEM_LOCK(&pAd->BcnRingLock); }\n'
            '#endif\n')
        cfg_source = f'drivers/net/wireless/mediatek/{radio}/ap/ap_cfg.c'
        (driver / 'ap/.ap_cfg.o.cmd').write_text(
            'cmd_ap/ap_cfg.o := ' + shlex.join([*command[:-1], cfg_source]) + '\n'
        )
        # Missing command must remain visible as unavailable beside compiled units.
        (driver / 'ap/ap_nps.c').write_text(
            'void tim_lock(void) { RTMP_SEM_LOCK(&pAd->BcnRingLock); }\n')
        for receiver in ('common/cmm_data.c', 'common/cmm_data_pci.c',
                         'tx_rx/wdev_rx.c', 'mcu/andes_core.c'):
            receiver_path = driver / receiver
            receiver_path.parent.mkdir(parents=True, exist_ok=True)
            receiver_path.write_text('int receiver_probe;\n')
            receiver_source = receiver_path.relative_to(kernel).as_posix()
            receiver_command = [*command[:-1], receiver_source]
            (receiver_path.parent / f'.{receiver_path.stem}.o.cmd').write_text(
                f'cmd_{receiver_path.stem}.o := '
                + shlex.join(receiver_command) + '\n'
            )
    return kernel


def run_case(base, radio, ceiling, require_three, expected_exit, features=()):
    kernel = make_fixture(base, radio, ceiling, features)
    output = base / 'report.json'
    command = [
        sys.executable, str(CHECKER), str(kernel), radio,
        '--compiler', COMPILER, '--output', str(output),
    ]
    if require_three:
        command.append('--require-three-bss')
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    report = json.loads(output.read_text(encoding='utf-8'))
    expected_limit = 16 if radio == 'mt76x3' else 8
    assert result.returncode == expected_exit, (result.stdout, result.stderr)
    assert report['probe_status'] == 'complete', report
    assert report['chip_source_bss_limit'] == expected_limit, report
    assert report['effective_source_config_bss_limit'] == min(ceiling, expected_limit), report
    assert report['source_config_allows_three_bss'] is (ceiling >= 3), report
    assert report['runtime_verified'] is False, report
    expected_features = {name: ('-D'+name in features or '-D'+name+'=0' in features)
                         for name in ('IFUP_IN_PROBE', 'MULTI_CORE_SUPPORT', 'KTHREAD_SUPPORT')}
    assert report['effective_lifecycle_macros'] == expected_features, report
    if radio == 'mt76x3':
        assert report['beacon_submit_probe']['status'] == 'complete', report
        assert report['beacon_submit_probe']['effective_beacon_offload_support'] is (
            '-DBCN_OFFLOAD_SUPPORT' in features
        ), report
        assert report['beacon_submit_probe']['effective_pci_support'] is (
            '-DRTMP_PCI_SUPPORT' in features
        ), report
        assert report['beacon_submit_probe']['effective_multi_core_support'] is (
            '-DMULTI_CORE_SUPPORT' in features
        ), report
        lock_probe = report['beacon_lock_units_probe']
        assert lock_probe['all_unit_flags_available'] is False, lock_probe
        assert set(lock_probe['units']) == {
            'ap/ap.c', 'ap/ap_cfg.c', 'ap/ap_nps.c', 'common/cmm_mac_pci.c'
        }, lock_probe
        for name in ('ap/ap.c', 'ap/ap_cfg.c', 'common/cmm_mac_pci.c'):
            assert lock_probe['units'][name]['status'] == 'complete', lock_probe
            assert lock_probe['units'][name]['effective_multi_core_support'] is (
                '-DMULTI_CORE_SUPPORT' in features
            ), lock_probe
        assert lock_probe['units']['ap/ap.c']['sites'][0][
            'active_after_directives'] is True, lock_probe
        assert [site['active_after_directives'] for site in
                lock_probe['units']['common/cmm_mac_pci.c']['sites']] == [
                    '-DRESOURCE_PRE_ALLOC' not in features, True
                ], lock_probe
        assert lock_probe['units']['ap/ap_cfg.c']['sites'][0][
            'active_after_directives'] is ('-DDBG' in features), lock_probe
        assert lock_probe['units']['ap/ap_nps.c']['status'] == 'unavailable', lock_probe
        assert lock_probe['units']['ap/ap_nps.c']['effective_multi_core_support'] is None, lock_probe
        assert lock_probe['units']['ap/ap_nps.c']['sites'][0][
            'active_after_directives'] is None, lock_probe
        receive_probe = report['txs_receive_units_probe']
        assert receive_probe['all_unit_flags_available'] is True, receive_probe
        assert set(receive_probe['units']) == {
            'common/cmm_data.c', 'common/cmm_data_pci.c',
            'tx_rx/wdev_rx.c', 'mcu/andes_core.c'
        }, receive_probe
        for unit in receive_probe['units'].values():
            assert unit['status'] == 'complete', unit
            assert unit['effective_mt_mac'] is True, unit
            assert unit['effective_pci_support'] is ('-DRTMP_PCI_SUPPORT' in features), unit
            assert unit['effective_andes_support'] is (
                '-DCONFIG_ANDES_SUPPORT' in features
            ), unit
    assert 'chip_runtime_bss_limit' not in report
    assert 'runtime_capacity_source_verified' not in report
    if require_three:
        assert report['three_bss_requirement_satisfied'] is (ceiling >= 3), report


def run_unavailable_case(base, fault, required):
    kernel = make_fixture(base, 'mt76x3', 16)
    driver = kernel / 'drivers/net/wireless/mediatek/mt76x3'
    command_file = driver / 'chips/.rtmp_chip.o.cmd'
    if fault == 'missing-command':
        command_file.unlink()
        expected_error = 'found 0'
    elif fault == 'ambiguous-command':
        (driver / '.rtmp_chip.o.cmd').write_bytes(command_file.read_bytes())
        expected_error = 'found 2'
    elif fault == 'wrong-compiler':
        command_file.write_text('cmd_probe := missing-capacity-compiler -c probe.c\n')
        expected_error = 'compiler is absent'
    else:
        raise AssertionError(f'Unknown fixture fault: {fault}')
    output = base / 'report.json'
    command = [sys.executable, str(CHECKER), str(kernel), 'mt76x3',
               '--compiler', COMPILER, '--output', str(output)]
    if required:
        command.append('--require-three-bss')
    result = subprocess.run(command, text=True, capture_output=True, check=False)
    assert result.returncode == (1 if required else 0), (result.stdout, result.stderr)
    report = json.loads(output.read_text(encoding='utf-8'))
    assert report['probe_status'] == 'unavailable', report
    assert report['effective_lifecycle_macros'] is None, report
    assert report['capacity_source_verified'] is False, report
    assert report['source_config_allows_three_bss'] is False, report
    assert report['runtime_verified'] is False, report
    assert report['three_bss_requirement_satisfied'] is (False if required else None), report
    assert expected_error in report['error'], report


def run_timeout_case(base):
    kernel = make_fixture(base, 'mt76x3', 16)
    output = base / 'report.json'
    args = [str(CHECKER), str(kernel), 'mt76x3', '--compiler', COMPILER,
            '--output', str(output), '--require-three-bss']
    with patch.object(sys, 'argv', args), patch.object(
            subprocess, 'run', side_effect=subprocess.TimeoutExpired('compiler', 60)) as compiler:
        try:
            runpy.run_path(str(CHECKER), run_name='__main__')
        except SystemExit as error:
            assert error.code == 1, error
        else:
            raise AssertionError('Required gate accepted a compiler timeout')
        assert compiler.call_args.kwargs['timeout'] == 60
    report = json.loads(output.read_text(encoding='utf-8'))
    assert report['probe_status'] == 'unavailable', report
    assert report['effective_lifecycle_macros'] is None, report
    assert report['three_bss_requirement_satisfied'] is False, report
    assert report['capacity_source_verified'] is False, report
    assert report['runtime_verified'] is False, report
    assert 'timed out' in report['error'], report


def run_observer_compile_cases(base):
    compile_probe=runpy.run_path(str(CHECKER),run_name='observer_fixture')['compile_main_observer']
    base.mkdir(parents=True)
    for mode in ('mips','host-object','compile-error'):
        def compiler(command,**kwargs):
            assert 'chips/original.c' not in command
            assert '-DMT7603' in command and '-c' in command
            assert kwargs['timeout']==60
            if mode=='compile-error':return subprocess.CompletedProcess(command,1,'','injected compile refusal')
            data=bytearray(20);data[:6]=b'\x7fELF\x01\x01'
            data[18:20]=(8 if mode=='mips' else 62).to_bytes(2,'little')
            Path(command[command.index('-o')+1]).write_bytes(data)
            return subprocess.CompletedProcess(command,0,'','')
        with patch.object(subprocess,'run',side_effect=compiler):
            try:
                result=compile_probe(Path(COMPILER),['-DMT7603','chips/original.c'],base,base/'report.json')
            except RuntimeError as error:
                assert mode!='mips'
                assert ('not ELF32' if mode=='host-object' else 'compile refusal') in str(error)
            else:
                assert mode=='mips' and result['status']=='compiled'
    # Ambiguous source arguments must fail before a compiler is called.
    with patch.object(subprocess,'run') as compiler:
        try:compile_probe(Path(COMPILER),['a.c','b.c'],base,base/'report.json')
        except RuntimeError:pass
        else:raise AssertionError('ambiguous source accepted')
        compiler.assert_not_called()


def run_receiver_unavailable_case(base):
    kernel = make_fixture(base, 'mt76x3', 16)
    driver = kernel / 'drivers/net/wireless/mediatek/mt76x3'
    (driver / 'mcu/.andes_core.o.cmd').unlink()
    probe = runpy.run_path(str(CHECKER), run_name='receiver_fixture')[
        'probe_txs_receive_units'
    ]
    report = probe(driver, kernel, Path(COMPILER))
    assert report['all_unit_flags_available'] is False, report
    assert report['units']['mcu/andes_core.c']['status'] == 'unavailable', report
    assert report['units']['mcu/andes_core.c']['effective_andes_support'] is None, report
    assert report['units']['common/cmm_data.c']['status'] == 'complete', report


def run_beacon_lock_inventory_in_memory_case():
    """Keep all seven known lock owners visible without any Kbuild commands."""
    from pathlib import PurePosixPath

    bodies = {
        'ap/ap_cfg.c': 'VOID Set_BcnStateCtrl_Proc() {\nRTMP_SEM_LOCK(&pAd->BcnRingLock);\n}',
        'ap/ap_nps.c': 'VOID RT28xx_UpdateTimToAsic() {\nRTMP_SEM_LOCK(&pAd->BcnRingLock);\n}',
        'common/cmm_data_pci.c': 'VOID RTMPHandleBcnDmaDoneInterrupt() {\nRTMP_SEM_LOCK(&pAd->BcnRingLock);\n}',
        'common/cmm_mac_pci.c': (
            'VOID RTMPFreeTxRxRingMemory() {\nRTMP_SEM_LOCK(&pAd->BcnRingLock);\n}\n'
            'VOID RTMPRingCleanUp() {\nRTMP_IRQ_LOCK(&pAd->BcnRingLock, flags);\n}\n'
            'VOID PDMAResetAndRecovery() {\nRTMP_IRQ_LOCK(&pAd->BcnRingLock, flags);\n}\n'
            'INT32 RT28xx_UpdateBeaconToAsic() {\nRTMP_SEM_LOCK(&pAd->BcnRingLock);\n}'
        ),
    }

    class Source:
        def __init__(self, name):
            self.name = name
            self.stem = PurePosixPath(name).stem

        def __lt__(self, other):
            return self.name < other.name

        def read_text(self, **_kwargs):
            return bodies[self.name]

        def relative_to(self, _driver):
            return PurePosixPath(self.name)

    class Driver:
        def rglob(self, pattern):
            assert pattern == '*.c'
            return [Source(name) for name in bodies]

    probe = runpy.run_path(str(CHECKER), run_name='lock_inventory_fixture')[
        'probe_beacon_lock_units'
    ]
    with patch.dict(probe.__globals__, {
            'probe_kbuild_macros': lambda *_args: (_ for _ in ()).throw(
                RuntimeError('missing object command'))}):
        report = probe(Driver(), Path('kernel'), Path(COMPILER))
    assert report['all_unit_flags_available'] is False, report
    assert set(report['units']) == set(bodies), report
    expected = {
        'ap/ap_cfg.c': [('Set_BcnStateCtrl_Proc', 'SEM')],
        'ap/ap_nps.c': [('RT28xx_UpdateTimToAsic', 'SEM')],
        'common/cmm_data_pci.c': [('RTMPHandleBcnDmaDoneInterrupt', 'SEM')],
        'common/cmm_mac_pci.c': [
            ('RTMPFreeTxRxRingMemory', 'SEM'),
            ('RTMPRingCleanUp', 'IRQ'),
            ('PDMAResetAndRecovery', 'IRQ'),
            ('RT28xx_UpdateBeaconToAsic', 'SEM'),
        ],
    }
    for name, sites in expected.items():
        unit = report['units'][name]
        assert unit['status'] == 'unavailable', unit
        assert unit['effective_multi_core_support'] is None, unit
        assert all(site['active_after_directives'] is None for site in unit['sites']), unit
        assert [(site['function'], site['form']) for site in unit['sites']] == sites, unit
        assert all(site['line'] > 0 for site in unit['sites']), unit


def run_beacon_lock_directives_in_memory_case():
    parser = runpy.run_path(str(CHECKER), run_name='directives_fixture')[
        'active_beacon_lock_owners'
    ]
    source = Path('kernel/ap/ap_cfg.c').resolve()
    kernel = Path('kernel').resolve()
    text = ('# 1 "ap/ap_cfg.c"\n'
            'INT32 active() {\n'
            'RTMP_SEM_LOCK(&pAd->BcnRingLock);\n'
            '# 10 "ap/ap_cfg.c"\n'
            'VOID other() {\n'
            '# 1 "ap/unrelated.h" 1\n'
            'RTMP_IRQ_LOCK(&pAd->BcnRingLock, flags);\n'
            '# 11 "ap/ap_cfg.c" 2\n'
            'RTMP_IRQ_LOCK(&pAd->BcnRingLock, flags);\n')
    assert dict(parser(text, source, kernel)) == {
        ('active', 'SEM'): 1, ('other', 'IRQ'): 1}
    try:
        parser('# 1 "ap/unrelated.h"\nRTMP_SEM_LOCK(&pAd->BcnRingLock);\n',
               source, kernel)
    except RuntimeError as error:
        assert 'no marker' in str(error), error
    else:
        raise AssertionError('Missing target source marker was accepted')


def run_duplicate_beacon_owner_in_memory_case():
    """A partial duplicate must be unknown for each individual source site."""
    from pathlib import PurePosixPath

    class Source:
        stem = 'ap_mbss'

        def read_text(self, **_kwargs):
            return ('VOID mbss_cr_disable() {\n'
                    'RTMP_SEM_LOCK(&pAd->BcnRingLock);\n'
                    'RTMP_SEM_LOCK(&pAd->BcnRingLock);\n}\n')

        def relative_to(self, _driver):
            return PurePosixPath('ap/ap_mbss.c')

    class Driver:
        def rglob(self, pattern):
            assert pattern == '*.c'
            return [Source()]

    probe = runpy.run_path(str(CHECKER), run_name='duplicate_fixture')[
        'probe_beacon_lock_units'
    ]
    for count, expected in ((0, False), (1, None), (2, True)):
        with patch.dict(probe.__globals__, {
                'probe_kbuild_macros': lambda *_args: ('cmd', ''),
                'probe_kbuild_active_beacon_owners': lambda *_args: (
                    'cmd', Counter({('mbss_cr_disable', 'SEM'): count}))}):
            report = probe(Driver(), Path('kernel'), Path(COMPILER))
        unit = report['units']['ap/ap_mbss.c']
        assert unit['status'] == 'complete', unit
        assert [site['active_after_directives'] for site in unit['sites']] == [
            expected, expected], unit
        assert unit['site_activity_complete'] is (expected is not None), unit
        assert report['all_site_activity_available'] is (expected is not None), report


if __name__ == '__main__':
    run_beacon_lock_inventory_in_memory_case()
    run_beacon_lock_directives_in_memory_case()
    run_duplicate_beacon_owner_in_memory_case()

    with tempfile.TemporaryDirectory(prefix='iot-capacity-selftest-') as temporary:
        root = Path(temporary)
        run_case(root / 'mt76x3-pass', 'mt76x3', 16, True, 0)
        run_case(root / 'mt76x2-diagnostic', 'mt76x2', 8, False, 0)
        run_case(root / 'mt76x3-fail', 'mt76x3', 2, True, 1)
        run_case(root / 'mt76x3-array-eight', 'mt76x3', 8, True, 0)
        run_case(root / 'mt76x3-probe-features', 'mt76x3', 16, True, 0,
                 ('-DIFUP_IN_PROBE', '-DMULTI_CORE_SUPPORT', '-DKTHREAD_SUPPORT=0',
                  '-DDBG', '-DRESOURCE_PRE_ALLOC'))
        run_case(root / 'mt76x3-beacon-offload', 'mt76x3', 16, True, 0,
                 ('-DBCN_OFFLOAD_SUPPORT', '-DRTMP_PCI_SUPPORT',
                  '-DCONFIG_ANDES_SUPPORT'))
        run_receiver_unavailable_case(root / 'mt76x3-receiver-unavailable')
        for fault in ('missing-command', 'ambiguous-command', 'wrong-compiler'):
            for required in (False, True):
                run_unavailable_case(root / f'{fault}-{required}', fault, required)
        run_timeout_case(root / 'compiler-timeout')
        run_observer_compile_cases(root / 'observer-control-cases')

    print('PASS IoT capacity probe MT76x2/MT7603 source checks and required-limit failure')
    print('PASS missing/ambiguous Kbuild and unavailable compiler refuse required capacity')
    print('PASS per-unit TxS receive macros and missing Andes command stay unavailable')
    print('PASS seven beacon lock owners remain inventoried without object commands')
    print('PASS directive-surviving lock calls map to source owners only')
    print('PASS partial duplicate owner stays unknown per source site')
    print('PASS observer compile runner: injected MIPS object accepted, host/error/ambiguous input rejected; actual target compiler not exercised')
