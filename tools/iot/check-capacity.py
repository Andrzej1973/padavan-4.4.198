#!/usr/bin/env python3
"""Report effective MBSS/beacon-array macros; never imply live BSS support."""
import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
import tempfile
from collections import Counter
from pathlib import Path


FUNCTION_DECLARATION = re.compile(
    r'^\s*(?:(?:static|inline|extern)\s+)*'
    r'(?:VOID|INT|INT16|INT32|INT64|BOOLEAN|NDIS_STATUS|'
    r'UCHAR|UINT|UINT16|UINT32|UINT64|LONG|ULONG|void|int|bool)\s+'
    r'([A-Za-z_]\w*)\s*\(')


def compile_main_observer(compiler, filtered, kernel, output):
    """Compile against recorded driver flags, never mutate the kernel tree."""
    sources=[i for i,arg in enumerate(filtered) if arg.endswith('.c')]
    if len(sources)!=1:
        raise RuntimeError('Expected one Kbuild C source for observer probe')
    flags=[arg for i,arg in enumerate(filtered) if i!=sources[0]]
    header=Path(__file__).with_name('mt7603-main-observe.h').resolve()
    if not header.is_file():raise RuntimeError('Observer header absent')
    output.parent.mkdir(parents=True,exist_ok=True)
    stage=Path(tempfile.mkdtemp(prefix='mt7603-main-observer-',dir=output.parent)).resolve()
    source=stage/'probe.c';obj=stage/'probe.o'
    source.write_text('#include "rt_config.h"\n#include "mt7603-main-observe.h"\n'
                      'int wr_main_observer_probe(PRTMP_ADAPTER ad) {\n'
                      ' return wr_iot_mt7603_main_config_observed(ad);\n}\n'
                      'int wr_bss_observer_probe(PRTMP_ADAPTER ad, PNET_DEV dev) {\n'
                      ' return wr_iot_mt7603_bss_config_observed(ad, dev, 2U);\n}\n',
                      encoding='utf-8')
    command=[str(compiler.resolve()),*flags,'-I'+str(header.parent),'-c',str(source),'-o',str(obj)]
    result=subprocess.run(command,cwd=kernel,text=True,capture_output=True,timeout=60)
    if result.returncode:
        raise RuntimeError('Actual-header observer compilation failed: '+result.stderr[-3000:])
    data=obj.read_bytes()
    if len(data)<20 or data[:6]!=b'\x7fELF\x01\x01' or int.from_bytes(data[18:20],'little')!=8:
        raise RuntimeError('Observer compiler output is not ELF32 little-endian MIPS')
    return {'status':'compiled','scope':'main and BSS observers with actual rt_config.h and rtmp_chip.o Kbuild flags; not whole-driver/runtime',
            'object':str(obj),'object_sha256':hashlib.sha256(data).hexdigest(),
            'header_sha256':hashlib.sha256(header.read_bytes()).hexdigest(),
            'command':command}


def recorded_kbuild_command(driver, kernel, compiler, source):
    """Return one verified target compiler command without output/dependency flags."""
    command_files = list(driver.rglob(f'.{source.stem}.o.cmd'))
    if len(command_files) != 1:
        raise RuntimeError(
            f'Expected one actual .{source.stem}.o.cmd under {driver}; found {len(command_files)}'
        )
    command_file = command_files[0]
    commands = re.findall(r'^cmd_.*? := (.+)$',
                          command_file.read_text(encoding='utf-8'), re.M)
    if len(commands) != 1:
        raise RuntimeError('Expected one Kbuild compiler command')
    argv = shlex.split(commands[0])
    if not argv:
        raise RuntimeError('Kbuild compiler command is empty')
    recorded = Path(argv[0])
    if not recorded.is_absolute():
        recorded = (kernel / recorded) if '/' in argv[0] or '\\' in argv[0] else Path(
            shutil.which(argv[0]) or ''
        )
    if not recorded.is_file() or recorded.resolve() != compiler.resolve():
        raise RuntimeError('Kbuild compiler differs from pinned compiler')
    if any(token in (';', '&&', '||', '|', '>', '<') for token in argv):
        raise RuntimeError('Unexpected compound Kbuild command')
    filtered = []
    index = 1
    while index < len(argv):
        token = argv[index]
        if token in ('-o', '-MF', '-MT', '-MQ'):
            index += 2
            continue
        if (token in ('-c', '-MD', '-MMD', '-MP')
                or token.startswith('-Wp,-MD,') or token.startswith('-Wp,-MMD,')):
            index += 1
            continue
        filtered.append(token)
        index += 1
    sources = [value for value in filtered if value.endswith('.c')]
    expected = source.relative_to(kernel).as_posix()
    recorded_source = Path(sources[0]) if len(sources) == 1 else None
    if recorded_source is not None and not recorded_source.is_absolute():
        recorded_source = kernel / recorded_source
    if recorded_source is None or recorded_source.resolve() != source.resolve():
        raise RuntimeError(f'Kbuild command has an unexpected source for {expected}')
    return command_file.relative_to(kernel).as_posix(), filtered


def probe_kbuild_macros(driver, kernel, compiler, source):
    """Preprocess one TU using its recorded Kbuild command, when available."""
    command, filtered = recorded_kbuild_command(driver, kernel, compiler, source)
    result = subprocess.run([str(compiler.resolve()), *filtered, '-E', '-dM'],
                            cwd=kernel, text=True, capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError('Target preprocessing failed: ' + result.stderr[-2000:])
    return command, result.stdout


def active_beacon_lock_owners(preprocessed, source, kernel):
    """Count surviving function/form pairs in the target source unit."""
    active = Counter()
    current_source = False
    source_seen = False
    function = None
    target = source.resolve()
    for line in preprocessed.splitlines():
        marker = re.match(r'^#\s+(\d+)\s+"([^"]+)"(?:\s|$)', line)
        if marker:
            name = marker.group(2)
            current_source = (not name.startswith('<') and
                              ((Path(name) if Path(name).is_absolute()
                                else kernel / name).resolve() == target))
            source_seen = source_seen or current_source
            continue
        if not current_source:
            continue
        declaration = FUNCTION_DECLARATION.match(line)
        if declaration:
            function = declaration.group(1)
        match = re.search(r'RTMP_(SEM|IRQ)_LOCK\s*\(\s*&pAd->BcnRingLock', line)
        if match:
            if function is None:
                raise RuntimeError('Directive output has a lock without a function owner')
            active[(function, match.group(1))] += 1
    if not source_seen:
        raise RuntimeError('Directive output has no marker for the target source')
    return active


def probe_kbuild_active_beacon_owners(driver, kernel, compiler, source):
    """Evaluate #if branches while retaining lock macro calls and line markers."""
    command, filtered = recorded_kbuild_command(driver, kernel, compiler, source)
    result = subprocess.run(
        [str(compiler.resolve()), *filtered, '-E', '-fdirectives-only'],
        # The pinned driver has non-UTF-8 bytes in comments. Preserve them
        # without changing ASCII line markers or lock call spelling.
        cwd=kernel, text=True, encoding='utf-8', errors='surrogateescape',
        capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError('Target directive preprocessing failed: ' + result.stderr[-2000:])
    return command, active_beacon_lock_owners(result.stdout, source, kernel)


def probe_beacon_submit_macros(driver, kernel, compiler):
    """Inspect the compiled PCI beacon submit unit, not a neighboring TU."""
    source = driver / 'common/cmm_mac_pci.c'
    command, macros = probe_kbuild_macros(driver, kernel, compiler, source)
    return {
        'status': 'complete',
        'source_command': command,
        'effective_beacon_offload_support': bool(re.search(
            r'^#define BCN_OFFLOAD_SUPPORT(?:[ \t]|$)', macros, re.M)),
        'effective_pci_support': bool(re.search(
            r'^#define RTMP_PCI_SUPPORT(?:[ \t]|$)', macros, re.M)),
        'effective_multi_core_support': bool(re.search(
            r'^#define MULTI_CORE_SUPPORT(?:[ \t]|$)', macros, re.M)),
        'scope': 'actual cmm_mac_pci.o Kbuild preprocessing; candidate/target compile and runtime unverified',
    }


def probe_beacon_lock_units(driver, kernel, compiler):
    """Inventory source-text lock sites; missing build commands stay unknown."""
    units = {}
    for source in sorted(driver.rglob('*.c')):
        body = source.read_text(encoding='utf-8', errors='replace')
        sites = []
        function = None
        for number, line in enumerate(body.splitlines(), 1):
            if line.lstrip().startswith(('/', '*')):
                continue
            declaration = FUNCTION_DECLARATION.match(line)
            if declaration:
                function = declaration.group(1)
            match = re.search(r'RTMP_(SEM|IRQ)_LOCK\s*\(\s*&pAd->BcnRingLock', line)
            if match:
                sites.append({'line': number, 'form': match.group(1),
                              'function': function})
        if not sites:
            continue
        relative = source.relative_to(driver).as_posix()
        try:
            command, macros = probe_kbuild_macros(driver, kernel, compiler, source)
            _, active_owners = probe_kbuild_active_beacon_owners(
                driver, kernel, compiler, source)
            source_owners = Counter((site['function'], site['form']) for site in sites)
            if any(site['function'] is None for site in sites):
                raise RuntimeError('Source lock has no function owner')
            if any(count > source_owners[owner]
                   for owner, count in active_owners.items()):
                raise RuntimeError(
                    f'Directive output has unmapped beacon lock owners: {dict(active_owners)}')
            for site in sites:
                owner = (site['function'], site['form'])
                active_count = active_owners[owner]
                site['active_after_directives'] = (
                    False if active_count == 0 else
                    True if active_count == source_owners[owner] else None)
            units[relative] = {
                'status': 'complete', 'source_command': command, 'sites': sites,
                'site_activity_complete': all(
                    site['active_after_directives'] is not None for site in sites),
                'effective_multi_core_support': bool(re.search(
                    r'^#define MULTI_CORE_SUPPORT(?:[ \t]|$)', macros, re.M)),
            }
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            for site in sites:
                site['active_after_directives'] = None
            units[relative] = {
                'status': 'unavailable', 'sites': sites,
                'site_activity_complete': False,
                'effective_multi_core_support': None,
                'error': str(error),
            }
    return {
        'units': units,
        'all_unit_flags_available': bool(units) and all(
            unit['status'] == 'complete' for unit in units.values()),
        'all_site_activity_available': bool(units) and all(
            unit['site_activity_complete'] for unit in units.values()),
        'scope': ('source-text lock sites plus actual per-unit Kbuild macros and '
                  'directive-survival; lock safety and runtime unverified'),
    }


def probe_txs_receive_units(driver, kernel, compiler):
    """Inventory exact target units that can feed the TxS parser."""
    units = {}
    for relative in (
            'common/cmm_data.c',
            'common/cmm_data_pci.c',
            'tx_rx/wdev_rx.c',
            'mcu/andes_core.c'):
        source = driver / relative
        try:
            command, macros = probe_kbuild_macros(driver, kernel, compiler, source)
            units[relative] = {
                'status': 'complete', 'source_command': command,
                'effective_mt_mac': bool(re.search(
                    r'^#define MT_MAC(?:[ \t]|$)', macros, re.M)),
                'effective_pci_support': bool(re.search(
                    r'^#define RTMP_PCI_SUPPORT(?:[ \t]|$)', macros, re.M)),
                'effective_andes_support': bool(re.search(
                    r'^#define CONFIG_ANDES_SUPPORT(?:[ \t]|$)', macros, re.M)),
            }
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
            units[relative] = {
                'status': 'unavailable',
                'effective_mt_mac': None,
                'effective_pci_support': None,
                'effective_andes_support': None,
                'error': str(error),
            }
    return {
        'units': units,
        'all_unit_flags_available': all(
            unit['status'] == 'complete' for unit in units.values()),
        'scope': ('actual per-unit Kbuild preprocessing only; MCU report '
                  'routing, queued-report drain and runtime unverified'),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kernel', type=Path)
    parser.add_argument('radio', choices=['mt76x2', 'mt76x3'])
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-commit')
    parser.add_argument('--check-main-observer',action='store_true',
                        help='also compile MT7603 observer with actual driver headers/flags')
    parser.add_argument(
        '--require-three-bss', action='store_true',
        help='fail unless source and effective target compile configuration allow at least three BSS',
    )
    args = parser.parse_args()

    root = args.kernel.resolve()
    driver = root / 'drivers/net/wireless/mediatek' / args.radio
    report = {
        'radio': args.radio,
        'probe_status': 'unavailable',
        'effective_mbss_support': None,
        'main_observer_probe': None,
        'effective_lifecycle_macros': None,
        'lifecycle_macro_scope': 'rtmp_chip.o preprocessing only; other translation units and runtime unverified',
        'effective_beacon_offload_support': None,
        'effective_pci_support': None,
        'beacon_macro_scope': 'rtmp_chip.o Kbuild command only; beacon submit translation unit unverified',
        'beacon_submit_probe': None,
        'beacon_lock_units_probe': None,
        'txs_receive_units_probe': None,
        'hardware_array_ceiling': None,
        'chip_source_bss_limit': None,
        'effective_source_config_bss_limit': None,
        'source_config_allows_three_bss': False,
        'three_bss_requirement': 'required' if args.require_three_bss else 'diagnostic',
        'three_bss_requirement_satisfied': None,
        'capacity_source_verified': False,
        'max_mesh_num': None,
        'max_apcli_num': None,
        'source_command': None,
        'source_commit': args.source_commit,
        'capacity_source_files': {},
        'runtime_verified': False,
        'scope': (
            'Effective Kbuild macros plus source-verified chip BSS-limit initializer; '
            'driver runtime, radio behavior, and live third BSS remain unverified'
        ),
    }

    try:
        def function_body(source, signature):
            # Strip comments before balancing braces so an example in a
            # comment cannot truncate or extend the function body.
            source = re.sub(r'/\*[\s\S]*?\*/|//[^\n]*', '', source)
            start = source.find(signature)
            opening = source.find('{', start) if start >= 0 else -1
            if opening < 0:
                raise RuntimeError(f'Missing source function: {signature}')
            depth = 0
            for position in range(opening, len(source)):
                if source[position] == '{':
                    depth += 1
                elif source[position] == '}':
                    depth -= 1
                    if depth == 0:
                        return source[opening:position + 1]
            raise RuntimeError(f'Unbalanced source function: {signature}')

        # Kbuild may store the command beside the source or in its output
        # directory. Find it under this radio source tree and reject ambiguity.
        command_files = list(driver.rglob('.rtmp_chip.o.cmd'))
        if len(command_files) != 1:
            raise RuntimeError(
                f'Expected one actual .rtmp_chip.o.cmd under {driver}; found {len(command_files)}'
            )
        command_file = command_files[0]
        report['source_command'] = str(command_file.relative_to(root))
        command_text = command_file.read_text(encoding='utf-8')
        commands = re.findall(r'^cmd_.*? := (.+)$', command_text, re.M)
        if len(commands) != 1:
            raise RuntimeError('Expected one actual Kbuild compiler command')

        argv = shlex.split(commands[0])
        if not argv:
            raise RuntimeError('Kbuild compiler command is empty')
        compiler = Path(argv[0])
        if not compiler.is_absolute():
            if '/' in argv[0] or '\\' in argv[0]:
                compiler = root / compiler
            else:
                resolved = shutil.which(argv[0])
                if not resolved:
                    raise RuntimeError('Kbuild compiler is absent from the build PATH')
                compiler = Path(resolved)
        if compiler.resolve() != args.compiler.resolve():
            raise RuntimeError('Kbuild compiler does not match requested pinned compiler')
        if any(token in (';', '&&', '||', '|', '>', '<') for token in argv):
            raise RuntimeError('Unexpected compound Kbuild command')

        filtered = []
        index = 1
        while index < len(argv):
            token = argv[index]
            if token in ('-o', '-MF', '-MT', '-MQ'):
                index += 2
                continue
            if (token in ('-c', '-MD', '-MMD', '-MP')
                    or token.startswith('-Wp,-MD,')
                    or token.startswith('-Wp,-MMD,')):
                index += 1
                continue
            filtered.append(token)
            index += 1

        result = subprocess.run(
            [str(args.compiler.resolve()), *filtered, '-E', '-dM'],
            cwd=root, text=True, capture_output=True, timeout=60,
        )
        if result.returncode:
            raise RuntimeError('Target preprocessing failed: ' + result.stderr[-2000:])

        macros = {
            match.group(1): match.group(2).strip()
            for match in re.finditer(
                r'^#define ([A-Za-z_][A-Za-z0-9_]*) (.*)$', result.stdout, re.M
            )
        }
        lifecycle_macros = {
            name: bool(re.search(r'^#define ' + re.escape(name) + r'(?:[ \t]|$)',
                                 result.stdout, re.M))
            for name in ('IFUP_IN_PROBE', 'MULTI_CORE_SUPPORT', 'KTHREAD_SUPPORT')
        }
        beacon_offload = bool(re.search(r'^#define BCN_OFFLOAD_SUPPORT(?:[ \t]|$)',
                                         result.stdout, re.M))
        pci_support = bool(re.search(r'^#define RTMP_PCI_SUPPORT(?:[ \t]|$)',
                                    result.stdout, re.M))
        # A valueless feature define may appear without a trailing value.
        mbss = bool(re.search(r'^#define MBSS_SUPPORT(?:\s|$)', result.stdout, re.M))
        ceiling_text = macros.get('HW_BEACON_MAX_NUM', '')
        ceiling = int(ceiling_text) if re.fullmatch(r'[0-9]+', ceiling_text) else None

        def read_source(relative):
            path = driver / relative
            text = path.read_text(encoding='utf-8')
            report['capacity_source_files'][str(path.relative_to(root))] = hashlib.sha256(
                path.read_bytes()
            ).hexdigest()
            return text

        definitions = read_source('include/rtmp_def.h')
        mbss_block = re.search(
            r'^#ifdef\s+MBSS_SUPPORT\b([\s\S]*?)^#else\b', definitions, re.M
        )
        if (not mbss_block
                or not re.search(r'#undef\s+MAX_MBSSID_NUM\b', mbss_block.group(1))
                or not re.search(
                    r'#define\s+MAX_MBSSID_NUM\s*\([^)]*\)\s*'
                    r'\(\(\s*__pAd\s*\)->chipCap\.BcnMaxNum\)',
                    mbss_block.group(1),
                )):
            raise RuntimeError('MBSS MAX_MBSSID_NUM no longer uses the chip BcnMaxNum limit')
        if not re.search(r'#define\s+MAX_MBSSID_NUM\s*\([^)]*\)\s+1', definitions):
            raise RuntimeError('Single-BSS fallback is missing from the driver header')

        chip_source = read_source('chips/rtmp_chip.c')
        if args.radio == 'mt76x2':
            chip_impl = read_source('chips/mt76x2.c')
            init_body = function_body(chip_impl, 'VOID mt76x2_init(')
            if init_body.count('rlt_bcn_buf_init(pAd);') != 1:
                raise RuntimeError('MT76x2 chip init no longer calls rlt_bcn_buf_init once')
            beacon_body = function_body(chip_source, 'VOID rlt_bcn_buf_init(')
            if not re.search(
                r'#if\s+defined\s*\(\s*MT7601\s*\)\s*\|\|\s*'
                r'defined\s*\(\s*MT76x2\s*\)[\s\S]*?BcnMaxHwNum\s*=\s*8\s*;',
                beacon_body,
            ):
                raise RuntimeError('MT76x2 eight-beacon chip branch changed')
            if not re.search(
                r'#ifdef\s+APCLI_SUPPORT\s+pChipCap->BcnMaxNum\s*=\s*'
                r'\(\s*8\s*-\s*MAX_MESH_NUM\s*\)\s*;\s*#else\s+'
                r'pChipCap->BcnMaxNum\s*=\s*\(\s*pChipCap->BcnMaxHwNum\s*'
                r'-\s*MAX_MESH_NUM\s*\)\s*;',
                beacon_body,
            ):
                raise RuntimeError('MT76x2 BSS-limit/APCLI reservation logic changed')
            if not re.search(r'^#define MT76x2(?:\s|$)', result.stdout, re.M):
                raise RuntimeError('Effective Kbuild command lacks the MT76x2 chip define')
            if not re.search(r'^#define RLT_MAC(?:\s|$)', result.stdout, re.M):
                raise RuntimeError('Effective Kbuild command lacks the RLT_MAC initializer guard')
            mesh_text = macros.get('MAX_MESH_NUM', '')
            if not re.fullmatch(r'[0-9]+', mesh_text):
                raise RuntimeError('Effective MAX_MESH_NUM is not a numeric constant')
            chip_limit = 8 - int(mesh_text)
        else:
            chip_impl = read_source('chips/mt7603.c')
            init_body = function_body(chip_impl, 'VOID mt7603_init(')
            if init_body.count('mt_bcn_buf_init(pAd);') != 1:
                raise RuntimeError('MT7603 chip init no longer calls mt_bcn_buf_init once')
            beacon_body = function_body(chip_source, 'VOID mt_bcn_buf_init(')
            if not re.search(r'BcnMaxHwNum\s*=\s*16\s*;[\s\S]*?BcnMaxNum\s*=\s*16\s*;', beacon_body):
                raise RuntimeError('MT7603 beacon initializer no longer reserves 16 BSS entries')
            if not re.search(r'^#define MT7603(?:\s|$)', result.stdout, re.M):
                raise RuntimeError('Effective Kbuild command lacks the MT7603 chip define')
            if not re.search(r'^#define MT_MAC(?:\s|$)', result.stdout, re.M):
                raise RuntimeError('Effective Kbuild command lacks the MT_MAC initializer guard')
            chip_limit = 16
            report['capacity_source_files'][str((driver / 'chips/mt7603.c').relative_to(root))] = hashlib.sha256(
                (driver / 'chips/mt7603.c').read_bytes()
            ).hexdigest()

        effective_limit = min(ceiling, chip_limit) if mbss and ceiling is not None else (1 if not mbss else None)
        report.update({
            'probe_status': 'complete',
            'effective_mbss_support': mbss,
            'effective_lifecycle_macros': lifecycle_macros,
            'effective_beacon_offload_support': beacon_offload,
            'effective_pci_support': pci_support,
            'hardware_array_ceiling': ceiling,
            'chip_source_bss_limit': chip_limit,
            'effective_source_config_bss_limit': effective_limit,
            'source_config_allows_three_bss': bool(
                effective_limit is not None and effective_limit >= 3
            ),
            'capacity_source_verified': True,
            'max_mesh_num': macros.get('MAX_MESH_NUM'),
            'max_apcli_num': macros.get('MAX_APCLI_NUM'),
        })
        if args.radio == 'mt76x3':
            try:
                report['beacon_submit_probe'] = probe_beacon_submit_macros(
                    driver, root, args.compiler)
            except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
                report['beacon_submit_probe'] = {'status': 'unavailable', 'error': str(error)}
            report['beacon_lock_units_probe'] = probe_beacon_lock_units(
                driver, root, args.compiler)
            report['txs_receive_units_probe'] = probe_txs_receive_units(
                driver, root, args.compiler)
        if args.check_main_observer:
            if args.radio!='mt76x3':raise RuntimeError('Main observer applies only to MT7603')
            report['main_observer_probe']=compile_main_observer(args.compiler,filtered,root,args.output.resolve())
        report['three_bss_requirement_satisfied'] = (
            report['source_config_allows_three_bss']
            if args.require_three_bss else None
        )
    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as error:
        report['error'] = str(error)
        report['probe_status'] = 'unavailable'
        if args.check_main_observer and report['main_observer_probe'] is None:
            report['main_observer_probe']={'status':'unavailable','error':str(error)}
        if args.require_three_bss:
            report['three_bss_requirement_satisfied'] = False

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    if report['probe_status'] != 'complete':
        print(f"UNAVAILABLE {args.radio} IoT radio-capacity probe: {report['error']}")
    elif report['source_config_allows_three_bss']:
        print(
            f"PASS {args.radio} MBSS source/config limit is "
            f"{report['effective_source_config_bss_limit']} BSS; radio runtime unverified"
        )
    else:
        print(f"NOT ESTABLISHED {args.radio} three-BSS source/config support; radio runtime unverified")

    if args.check_main_observer and (report['main_observer_probe'] or {}).get('status')!='compiled':
        raise SystemExit(1)
    if args.require_three_bss and report['three_bss_requirement_satisfied'] is not True:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
