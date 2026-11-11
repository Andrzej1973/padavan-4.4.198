#!/usr/bin/env python3
"""Execute actual baseline and transformed commit with deterministic host I/O."""
import hashlib
import importlib.util
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile

here = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('commit_order', here / 'prepare-nvram-commit-order.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with tarfile.open(sys.argv[1]) as archive:
    original = archive.extractfile('trunk/linux-4.4.x/drivers/nvram/nvram_linux.c').read().decode()
patched = module.transform(original)
try:
    module.transform(patched)
except ValueError:
    pass
else:
    raise AssertionError('Repeated transformation must reject changed anchors')
fixture = (here / 'nvram-commit-order-fixture.c.inc').read_text()
with tempfile.TemporaryDirectory(prefix='wr-nvram-commit-order-') as scratch:
    root = Path(scratch)
    for fixed, source in enumerate((original, patched)):
        start = source.index('nvram_commit(void)\n{')
        body = 'static int\n' + source[start:source.index('\n}', start) + 2]
        cfile = root / f'commit-{fixed}.c'
        binary = root / f'commit-{fixed}'
        cfile.write_text(f'#define FIXED {fixed}\n' + fixture.replace('/* ACTUAL_COMMIT */', body))
        subprocess.run(['gcc', '-std=gnu11', '-pthread', '-Wall', '-Wextra', '-Werror', '-fsanitize=address,undefined', '-fno-pie', '-no-pie', str(cfile), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=15)
    print('Owned scratch bytes removed', sum(p.stat().st_size for p in root.iterdir()))
assert not root.exists()
print('Original source SHA256', hashlib.sha256(original.encode()).hexdigest())
print('Candidate source SHA256', hashlib.sha256(patched.encode()).hexdigest())
