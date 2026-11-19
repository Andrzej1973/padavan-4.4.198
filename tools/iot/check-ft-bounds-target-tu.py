#!/usr/bin/env python3
"""Compile the prepared FT ingress/consumer/insertion pair with actual Kbuild flags.

Temporary MIPS objects only. This does not install a module or replace an image.
"""
import argparse
import hashlib
import json
import re
import runpy
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
for name in ('kernel', 'driver', 'compiler', 'output'):
    p.add_argument('--'+name, type=Path, required=True)
a = p.parse_args()
root = a.kernel.resolve()
driver = a.driver.resolve()
compiler = a.compiler.resolve()
here = Path(__file__).resolve().parent
unwrap = runpy.run_path(str(here/'kbuild-compiler.py'))['unwrap_ccache']
source_rel = {
    'ft': Path('common/ft.c'),
    'mlme': Path('common/mlme.c'),
    'mgmt_entrytb': Path('mgmt/mgmt_entrytb.c'),
    'rtmp_init': Path('common/rtmp_init.c'),
}
report = {
    'status': 'failed',
    'scope': 'Prepared FT RRB and ordinary-RX ingress, FT action consumer, and scoped first-peer insertion temporary TUs only',
    'module_installed': False,
    'firmware_image_verified': False,
    'runtime_verified': False,
    'translation_units': {},
}


def command(unit):
    matches = list(driver.rglob('.'+unit+'.o.cmd'))
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one active '+unit+' Kbuild command')
    raw = matches[0].read_bytes()
    lines = re.findall(r'^cmd_.*? := (.+)$', raw.decode(), re.M)
    if len(lines) != 1:
        raise RuntimeError('Expected one '+unit+' compiler command')
    argv = unwrap(shlex.split(lines[0]))
    tool = Path(argv[0])
    if any(x in (';', '&&', '||', '|', '>', '<') for x in argv):
        raise RuntimeError('Unsupported shell operator in '+unit+' Kbuild command')
    if not tool.is_absolute():
        resolved = str(root/tool) if '/' in argv[0] else shutil.which(argv[0])
        tool = Path(resolved or '')
    if tool.resolve() != compiler:
        raise RuntimeError(unit+' compiler identity mismatch')
    filtered, sources, i = [], [], 1
    while i < len(argv):
        token = argv[i]
        if token in ('-o', '-MF', '-MT', '-MQ'):
            i += 2
            continue
        if token in ('-c', '-MD', '-MMD', '-MP') or token.startswith(('-Wp,-MD,', '-Wp,-MMD,')):
            i += 1
            continue
        if token.endswith('.c'):
            sources.append(token)
        else:
            filtered.append(token)
        i += 1
    if len(sources) != 1:
        raise RuntimeError('Expected one '+unit+' source')
    source = Path(sources[0])
    source = source if source.is_absolute() else root/source
    expected = driver/source_rel[unit]
    if source.resolve() != expected.resolve():
        raise RuntimeError('Unexpected '+unit+' source identity: '+str(source))
    return raw, tool.resolve(), filtered, source


def symbol_rows(obj, symbol):
    output = subprocess.run(['readelf', '-Ws', str(obj)], text=True,
                            capture_output=True, check=True).stdout
    return [line.split() for line in output.splitlines()
            if len(line.split()) >= 8 and line.split()[-1] == symbol]


try:
    commands = {unit: command(unit) for unit in source_rel}
    originals = {unit: item[3].read_bytes() for unit, item in commands.items()}

    # The candidate driver already contains the association-generation and peer
    # owner predecessors. Add the pending BSS+MAC storage and insertion clone on
    # top of that exact candidate, and shadow both native structure headers.
    insert_compose = runpy.run_path(str(here/'ft-pending-insert-composition.py'))['compose']
    pending_changes = insert_compose({}, driver, here)
    pending_enqueue = runpy.run_path(str(here/'ft-pending-enqueue-composition.py'))
    mlme_header = (driver/'include/mlme.h').read_text()
    mlme_header = pending_enqueue['queue_fields'](mlme_header)
    mlme_header = pending_enqueue['queue_closed_field'](mlme_header)

    enqueue = runpy.run_path(str(here/'ft-enqueue-generation-composition.py'))
    mlme = pending_enqueue['lifecycle'](originals['mlme'].decode())
    mlme, active_prototype = enqueue['compose'](mlme)
    mlme, pending_prototype = pending_enqueue['compose'](mlme)
    mlme = runpy.run_path(str(here/'ft-rx-generation-composition.py'))['compose'](
        mlme, active_prototype, pending_prototype)

    insert_prototype = '''#ifdef DOT11R_FT_SUPPORT
struct wr_ft_pending_peer_scope;
MAC_TABLE_ENTRY *wr_ft_pending_insert(RTMP_ADAPTER *,UCHAR *,struct wifi_dev *,
 const struct wr_ft_pending_token *,struct wr_ft_pending_peer_scope *);
#endif'''
    ft = runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose'](
        originals['ft'].decode())
    ft = enqueue['bind_ft'](ft, active_prototype, pending_prototype, insert_prototype)
    ft, _ = runpy.run_path(str(here/'ra2-ft-mutation-composition.py'))['compose'](ft)
    include = '#include "rt_config.h"'
    if ft.count(include) != 1:
        raise RuntimeError('FT configuration include changed')
    ft = ft.replace(include, include +
        '\n#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)\n'
        '#include "ra2-mutation-admission-kernel.h"\n#endif', 1)

    prepared = {
        'ft': ft,
        'mlme': mlme,
        'mgmt_entrytb': pending_changes['mgmt/mgmt_entrytb.c'],
        'rtmp_init': pending_changes['common/rtmp_init.c'],
    }
    with tempfile.TemporaryDirectory(prefix='wr-ft-generation-target-') as td:
        temp = Path(td)
        # rt_config.h is copied beside the shadow rtmp/mlme headers so quoted
        # includes resolve consistently; remaining vendor headers fall through
        # to the exact original Kbuild include directories.
        for name, data in (
            ('rt_config.h', (driver/'include/rt_config.h').read_bytes()),
            ('rtmp.h', pending_changes['include/rtmp.h'].encode()),
            ('mlme.h', mlme_header.encode()),
        ):
            (temp/name).write_bytes(data)
        for name in (
            'ft-action-bounds.h', 'ft-ie-span.h', 'ft-subelement-bounds.h',
            'ft-request-ie-admission.h', 'ft-peer-generation.h',
            'ft-pending-peer-scope.h', 'ft-pending-identity.h',
            'ft-pending-queue.h', 'assoc-generation.h',
            'assoc-generation-kernel.h', 'peer-table-owner.h',
            'peer-close-executor.h', 'ra2-mutation-admission-kernel.h',
        ):
            shutil.copyfile(here/name, temp/name)

        for unit, changed in prepared.items():
            raw, tool, filtered, _source = commands[unit]
            candidate = temp/(unit+'.c')
            obj = temp/(unit+'.o')
            candidate.write_text(changed)
            flags = [str(tool), '-I'+str(temp), *filtered, str(candidate)]
            macros = subprocess.run([*flags, '-E', '-dM'], cwd=root,
                                    text=True, capture_output=True, timeout=90)
            if macros.returncode:
                raise RuntimeError(unit+' preprocessing failed: '+macros.stderr[-4000:])
            required = ('DOT11R_FT_SUPPORT', 'CONFIG_AP_SUPPORT', 'MT7603',
                        'MT_MAC', 'RTMP_PCI_SUPPORT')
            effective = {name: bool(re.search(r'^#define '+name+r'(?:\s|$)',
                                  macros.stdout, re.M)) for name in required}
            if not all(effective.values()):
                raise RuntimeError(unit+' target features inactive: '+str(effective))
            build = subprocess.run([*flags, '-c', '-o', str(obj)], cwd=root,
                                   text=True, capture_output=True, timeout=150)
            if build.returncode:
                raise RuntimeError(unit+' target compilation failed: '+build.stderr[-8000:])
            data = obj.read_bytes()
            if data[:6] != b'\x7fELF\x01\x01' or int.from_bytes(data[18:20], 'little') != 8:
                raise RuntimeError('Expected ELF32 LE MIPS '+unit+' object')
            receipts = {}
            for name in ('wr_ft_mlme_enqueue_for_recv',
                         'wr_ft_pending_enqueue_for_recv',
                         'wr_ft_pending_insert'):
                rows = symbol_rows(obj, name)
                if rows:
                    if len(rows) != 1 or rows[0][4] != 'GLOBAL':
                        raise RuntimeError(unit+' has missing/ambiguous global '+name)
                    receipts[name] = {'ndx': rows[0][6], 'type': rows[0][3],
                                      'binding': rows[0][4]}
            hard_retry_flags = [str(tool), '-I'+str(temp), *filtered,
                                '-DR1KH_HARD_RETRY', str(candidate)]
            hard_retry_macros = subprocess.run(
                [*hard_retry_flags, '-E', '-dM'], cwd=root,
                text=True, capture_output=True, timeout=90)
            if hard_retry_macros.returncode:
                raise RuntimeError(unit+' R1KH_HARD_RETRY preprocessing failed: '
                                   +hard_retry_macros.stderr[-4000:])
            if not re.search(r'^#define R1KH_HARD_RETRY(?:\s|$)',
                             hard_retry_macros.stdout, re.M):
                raise RuntimeError(unit+' R1KH_HARD_RETRY variant inactive')
            hard_retry_obj = temp/(unit+'-r1kh-hard-retry.o')
            hard_retry_build = subprocess.run(
                [*hard_retry_flags[:-1], '-c', '-o', str(hard_retry_obj),
                 str(candidate)], cwd=root, text=True, capture_output=True,
                timeout=150)
            if hard_retry_build.returncode:
                raise RuntimeError(unit+' R1KH_HARD_RETRY target compilation failed: '
                                   +hard_retry_build.stderr[-8000:])
            hard_retry_data = hard_retry_obj.read_bytes()
            if (hard_retry_data[:6] != b'\x7fELF\x01\x01' or
                    int.from_bytes(hard_retry_data[18:20], 'little') != 8):
                raise RuntimeError('Expected ELF32 LE MIPS '+unit+
                                   ' R1KH_HARD_RETRY object')
            hard_retry_receipts = {}
            for name in ('wr_ft_mlme_enqueue_for_recv',
                         'wr_ft_pending_enqueue_for_recv',
                         'wr_ft_pending_insert'):
                rows = symbol_rows(hard_retry_obj, name)
                if rows:
                    if len(rows) != 1 or rows[0][4] != 'GLOBAL':
                        raise RuntimeError(unit+' R1KH_HARD_RETRY has missing/ambiguous global '+name)
                    hard_retry_receipts[name] = {
                        'ndx': rows[0][6], 'type': rows[0][3],
                        'binding': rows[0][4],
                    }
            report['translation_units'][unit] = {
                'effective_macros': effective,
                'r1kh_hard_retry_variant': {
                    'enabled': True,
                    'object_sha256': hashlib.sha256(hard_retry_data).hexdigest(),
                    'object_bytes': len(hard_retry_data),
                    'ft_symbols': hard_retry_receipts,
                },
                'command_sha256': hashlib.sha256(raw).hexdigest(),
                'source_sha256': hashlib.sha256(originals[unit]).hexdigest(),
                'prepared_source_sha256': hashlib.sha256(changed.encode()).hexdigest(),
                'object_sha256': hashlib.sha256(data).hexdigest(),
                'object_bytes': len(data),
                'ft_symbols': receipts,
            }
            a.output.parent.mkdir(parents=True, exist_ok=True)
            a.output.with_suffix('.'+unit+'.macros.txt').write_text(macros.stdout)

        contracts = (
            ('ft', 'wr_ft_mlme_enqueue_for_recv', 'mlme'),
            ('ft', 'wr_ft_pending_enqueue_for_recv', 'mlme'),
            ('ft', 'wr_ft_pending_insert', 'mgmt_entrytb'),
        )
        for consumer, name, provider in contracts:
            for variant in ('ft_symbols', 'r1kh_hard_retry_variant'):
                use_table = report['translation_units'][consumer][variant]
                define_table = report['translation_units'][provider][variant]
                if variant == 'r1kh_hard_retry_variant':
                    use_table = use_table['ft_symbols']
                    define_table = define_table['ft_symbols']
                use = use_table.get(name)
                define = define_table.get(name)
                if not use or use['ndx'] != 'UND':
                    raise RuntimeError(consumer+' '+variant+' must reference '+name+' as undefined')
                if not define or define['ndx'] == 'UND' or define['type'] != 'FUNC':
                    raise RuntimeError(provider+' '+variant+' must define '+name+' as global FUNC')

    for unit, item in commands.items():
        if item[3].read_bytes() != originals[unit]:
            raise RuntimeError('Original '+unit+' source changed during temporary probe')
    report['status'] = 'passed'
except (OSError, RuntimeError, ValueError, KeyError, subprocess.SubprocessError) as error:
    report['error'] = str(error)

a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(json.dumps(report, indent=2)+'\n')
print(report['status']+' prepared FT/MLME/insertion generation MIPS TUs; driver/image unchanged')
if report.get('error'):
    print(report['error'])
raise SystemExit(0 if report['status'] == 'passed' else 1)
