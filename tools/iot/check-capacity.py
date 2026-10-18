#!/usr/bin/env python3
"""Report effective MBSS/beacon-array macros; never imply live BSS support."""
import argparse
import hashlib
import json
import re
import shlex
import shutil
import subprocess
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('kernel', type=Path)
    parser.add_argument('radio', choices=['mt76x2', 'mt76x3'])
    parser.add_argument('--compiler', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--source-commit')
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
            cwd=root, text=True, capture_output=True,
        )
        if result.returncode:
            raise RuntimeError('Target preprocessing failed: ' + result.stderr[-2000:])

        macros = {
            match.group(1): match.group(2).strip()
            for match in re.finditer(
                r'^#define ([A-Za-z_][A-Za-z0-9_]*) (.*)$', result.stdout, re.M
            )
        }
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
        report['three_bss_requirement_satisfied'] = (
            report['source_config_allows_three_bss']
            if args.require_three_bss else None
        )
    except (OSError, RuntimeError, ValueError) as error:
        report['error'] = str(error)
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

    if args.require_three_bss and report['three_bss_requirement_satisfied'] is not True:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
