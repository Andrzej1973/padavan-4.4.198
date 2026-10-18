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


ROOT = Path(__file__).resolve().parents[2]
CHECKER = ROOT / 'tools/iot/check-capacity.py'
COMPILER = (os.environ.get('CC')
            or shutil.which('cc')
            or shutil.which('gcc')
            or shutil.which('clang'))
if not COMPILER:
    raise SystemExit('A host C compiler is required for the capacity self-test')


def make_fixture(base, radio, ceiling):
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
        *defines, '-c', source_path,
    ]
    # Kbuild records shell commands in POSIX form. On Windows, keep drive
    # paths absolute while avoiding backslashes that POSIX shlex treats as
    # escape characters when the checker reads the synthetic .cmd file.
    command[0] = command[0].replace('\\', '/')
    (chips / '.rtmp_chip.o.cmd').write_text(
        'cmd_chips/rtmp_chip.o := ' + shlex.join(command) + '\n'
    )
    return kernel


def run_case(base, radio, ceiling, require_three, expected_exit):
    kernel = make_fixture(base, radio, ceiling)
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
    assert report['capacity_source_verified'] is False, report
    assert report['source_config_allows_three_bss'] is False, report
    assert report['runtime_verified'] is False, report
    assert report['three_bss_requirement_satisfied'] is (False if required else None), report
    assert expected_error in report['error'], report


with tempfile.TemporaryDirectory(prefix='iot-capacity-selftest-') as temporary:
    root = Path(temporary)
    run_case(root / 'mt76x3-pass', 'mt76x3', 16, True, 0)
    run_case(root / 'mt76x2-diagnostic', 'mt76x2', 8, False, 0)
    run_case(root / 'mt76x3-fail', 'mt76x3', 2, True, 1)
    run_case(root / 'mt76x3-array-eight', 'mt76x3', 8, True, 0)
    for fault in ('missing-command', 'ambiguous-command', 'wrong-compiler'):
        for required in (False, True):
            run_unavailable_case(root / f'{fault}-{required}', fault, required)

print('PASS IoT capacity probe MT76x2/MT7603 source checks and required-limit failure')
print('PASS missing/ambiguous Kbuild and unavailable compiler refuse required capacity')
