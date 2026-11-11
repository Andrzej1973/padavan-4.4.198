#!/usr/bin/env python3
"""Compile isolated NVRAM batch/commit-order TU with configured target Kbuild."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source', type=Path)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = args.source.resolve(strict=True)
output = args.output.resolve()
output.mkdir(parents=True, exist_ok=True)
kernel = root / 'trunk/linux-4.4.x'
production = kernel / 'drivers/nvram'
spec = importlib.util.spec_from_file_location('nvram_batch', Path(__file__).with_name('prepare-nvram-batch-candidate.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
watched = [production / 'nvram_linux.c', production / 'nvram.c', production / 'nvram_linux.o',
           kernel / '.config', kernel / 'vmlinux']
watched += list((root / 'trunk/images').glob('*.trx'))
before = {str(p.relative_to(root)): digest(p) for p in watched}
report = {'scope': 'Isolated NVRAM batch/commit-order translation unit; no ioctl, not linked or installed',
          'repository_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=Path(__file__).resolve().parents[2], text=True).strip(),
          'production_before': before, 'target_compiled': False,
          'production_installed': False, 'runtime_verified': False, 'scratch_removed': False}
try:
    compiler = next((root / 'toolchain/toolchain-mipsel').glob('**/bin/mipsel-linux-uclibc-gcc'))
    compiler = compiler.absolute()  # Preserve compiler basename and tool prefix.
    cross = str(compiler)[:-3]
    with tempfile.TemporaryDirectory(prefix='wr-nvram-order-', dir=kernel / 'drivers') as scratch:
        target = Path(scratch)
        for name in ('nvram.c', 'nvram_linux.c', 'Makefile'):
            shutil.copyfile(production / name, target / name)
        source = target / 'nvram_linux.c'
        source.write_text(module.transform(source.read_text()))
        report['candidate_source_sha256'] = digest(source)
        obj = target / 'nvram_linux.o'
        command = ['make', '-C', str(kernel), 'ARCH=mips', 'CROSS_COMPILE=' + cross,
                   str(obj.relative_to(kernel))]
        report['command'] = command
        with (output / 'compile.log').open('w') as log:
            result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT)
        report['compile_exit_code'] = result.returncode
        if result.returncode:
            print('\n'.join((output / 'compile.log').read_text(errors='replace').splitlines()[-80:]))
            raise RuntimeError('Isolated NVRAM Kbuild failed; see compile.log')
        data = obj.read_bytes()
        if data[:6] != b'\x7fELF\x01\x01' or int.from_bytes(data[18:20], 'little') != 8:
            raise RuntimeError('NVRAM candidate is not ELF32LE MIPS')
        if int.from_bytes(data[16:18], 'little') != 1:
            raise RuntimeError('NVRAM candidate must be relocatable object')
        symbols = subprocess.check_output([cross + 'nm', '--defined-only', str(obj)], text=True)
        if not any(line.split()[-2:] == ['T', 'wr_nvram_batch_candidate'] for line in symbols.splitlines()):
            raise RuntimeError('Compiled NVRAM batch function missing from object')
        (output / 'defined-symbols.txt').write_text(symbols)
        report['batch_core_sha256'] = digest(Path(__file__).with_name('nvram-batch-core.c.inc'))
        report.update(target_compiled=True, object_bytes=len(data), object_sha256=digest(obj))
        shutil.copyfile(obj, output / 'nvram-commit-order.o')
        report['scratch_bytes'] = sum(p.stat().st_size for p in target.rglob('*') if p.is_file())
    report['scratch_removed'] = not target.exists()
finally:
    if 'target' in locals():
        report['scratch_removed'] = not target.exists()
    report['production_after'] = {str(p.relative_to(root)): digest(p) for p in watched}
    report['production_unchanged'] = report['production_after'] == before
    (output / 'result.json').write_text(json.dumps(report, indent=2) + '\n')
    if not report['production_unchanged']:
        raise RuntimeError('Production NVRAM/config/kernel/image changed during candidate compile')
print('PASS isolated NVRAM target object; production unchanged; runtime unverified')
