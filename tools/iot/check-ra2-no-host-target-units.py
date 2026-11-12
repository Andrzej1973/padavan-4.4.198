#!/usr/bin/env python3
"""Compile the separate ra2 experiment using recorded vendor Kbuild commands."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import runpy
import shlex
import shutil
import subprocess
import tempfile


def remap_driver_argument(value, driver, relative_driver, experiment):
    """Rewrite recorded driver paths, including an include of its root."""
    for old in (str(driver), relative_driver):
        value = value.replace(old + '/', str(experiment) + '/')
        if value == old:
            value = str(experiment)
        elif value in ('-I' + old, '-iquote' + old, '-isystem' + old):
            value = value[:-len(old)] + str(experiment)
    return value


def verify_dependencies(text, kernel, driver, experiment, expected):
    """Hash experimental inputs actually read by the compiler."""
    flat = text.replace('\\\n', ' ')
    if ': ' not in flat:
        raise RuntimeError('Missing compiler dependency target')
    inputs = shlex.split(flat.split(': ', 1)[1])
    verified = {}
    for name in inputs:
        path = Path(name)
        path = (path if path.is_absolute() else kernel / path).resolve()
        if path.is_relative_to(driver):
            raise RuntimeError('Baseline driver dependency used by experiment')
        if path.is_relative_to(experiment):
            relative = str(path.relative_to(experiment))
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if expected.get(relative) != digest:
                raise RuntimeError('Experimental dependency differs from manifest')
            verified[relative] = digest
    if not verified:
        raise RuntimeError('No experimental dependencies recorded')
    return verified


parser = argparse.ArgumentParser(description=__doc__)
for name in ('kernel', 'driver', 'experiment', 'compiler', 'output'):
    parser.add_argument('--' + name, type=Path, required=True)
args = parser.parse_args()
kernel = args.kernel.resolve()
driver = args.driver.resolve()
experiment = args.experiment.resolve()
compiler = args.compiler.resolve()
unwrap = runpy.run_path(str(Path(__file__).with_name('kbuild-compiler.py')))['unwrap_ccache']
units = ('mac/mt_mac.c', 'tx_rx/txs.c', 'ap/ap_connect.c', 'common/cmm_mac_pci.c')
report = {'status': 'failed', 'scope': 'Four experimental vendor translation units',
          'units': {}, 'runtime_verified': False, 'activation_ready': False}
config = (kernel / '.config').read_bytes()
try:
    manifest = json.loads(Path(str(experiment) + '.manifest.json').read_text())
    actual = {str(path.relative_to(experiment)): hashlib.sha256(path.read_bytes()).hexdigest()
              for path in experiment.rglob('*') if path.is_file()}
    if actual != manifest['candidate_driver_sha256'] or manifest['ra2_no_host_experiment']['activation_ready'] is not False:
        raise RuntimeError('Experimental source identity mismatch')
    relative_driver = str(driver.relative_to(kernel))
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='wr-ra2-target-objects-') as scratch:
        for unit in units:
            command_file = driver / str(Path(unit).parent) / ('.' + Path(unit).stem + '.o.cmd')
            commands = re.findall(r'^cmd_.*? := (.+)$', command_file.read_text(), re.M)
            if len(commands) != 1:
                raise RuntimeError('Expected one Kbuild command for ' + unit)
            argv = unwrap(shlex.split(commands[0]))
            tool = Path(argv[0])
            if not tool.is_absolute():
                tool = kernel / tool if '/' in argv[0] else Path(shutil.which(argv[0]) or '')
            if tool.resolve() != compiler:
                raise RuntimeError('Compiler mismatch for ' + unit)
            filtered = []
            source_count = 0
            index = 1
            while index < len(argv):
                value = argv[index]
                if value in ('-o', '-MF', '-MT', '-MQ'):
                    index += 2
                    continue
                index += 1
                if value in ('-c', '-MD', '-MMD', '-MP') or value.startswith(('-Wp,-MD,', '-Wp,-MMD,')):
                    continue
                if value in (';', '&&', '||', '|', '>', '<'):
                    raise RuntimeError('Unexpected shell token')
                if value.endswith('.c'):
                    path = Path(value)
                    path = path if path.is_absolute() else kernel / path
                    if path.resolve() != driver / unit:
                        raise RuntimeError('Unexpected source in Kbuild command')
                    value = str(experiment / unit)
                    source_count += 1
                else:
                    value = remap_driver_argument(value, driver, relative_driver, experiment)
                filtered.append(value)
            if source_count != 1:
                raise RuntimeError('Missing source for ' + unit)
            macros = subprocess.run([str(compiler), *filtered, '-E', '-dM'],
                                    cwd=kernel, capture_output=True, text=True, timeout=120)
            label = unit.replace('/', '_')
            (args.output / (label + '.macros.txt')).write_text(macros.stdout)
            if macros.returncode:
                (args.output / (label + '.log')).write_text(macros.stderr)
                raise RuntimeError('Preprocessing failed for ' + unit)
            required = ('MT7603', 'MT_MAC', 'RTMP_PCI_SUPPORT', 'RTMP_MAC_PCI', 'CONFIG_AP_SUPPORT')
            effective = {name: bool(re.search(r'^#define ' + name + r'(?:\s|$)', macros.stdout, re.M))
                         for name in required}
            if not all(effective.values()):
                raise RuntimeError('Experimental MT7603 PCI AP branches excluded for ' + unit)
            obj = Path(scratch) / (Path(unit).stem + '.o')
            dependencies = args.output.resolve() / (label + '.d')
            command = [str(compiler), *filtered, '-MD', '-MF', str(dependencies), '-c', '-o', str(obj)]
            result = subprocess.run(command, cwd=kernel, capture_output=True, text=True, timeout=180)
            (args.output / (label + '.log')).write_text(result.stdout + result.stderr)
            if result.returncode:
                raise RuntimeError('Compilation failed for ' + unit)
            verified_dependencies = verify_dependencies(dependencies.read_text(), kernel, driver,
                                                        experiment, actual)
            data = obj.read_bytes()
            if data[:6] != b'\x7fELF\x01\x01' or int.from_bytes(data[18:20], 'little') != 8:
                raise RuntimeError('Expected ELF32 little-endian MIPS for ' + unit)
            shutil.copyfile(obj, args.output / (label + '.o'))
            report['units'][unit] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                                     'command': command, 'effective_macros': effective,
                                     'macro_sha256': hashlib.sha256(macros.stdout.encode()).hexdigest(),
                                     'verified_dependencies': verified_dependencies}
    if (kernel / '.config').read_bytes() != config:
        raise RuntimeError('Kernel configuration changed')
    report['status'] = 'passed'
except (OSError, ValueError, KeyError, RuntimeError, subprocess.SubprocessError) as error:
    report['error'] = str(error)
finally:
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(report['status'] + ' experimental ra2 target translation units')
raise SystemExit(report['status'] != 'passed')
