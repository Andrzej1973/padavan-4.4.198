#!/usr/bin/env python3
"""Verify exact readback source capability including altered and linked input refusal."""
from pathlib import Path
import runpy
import sys
import tempfile

here=Path(__file__).resolve().parent
shared=here.parent/'band-steering'
guard=runpy.run_path(str(here/'native-flash-source-guard.py'))
source=Path(sys.argv[1]).read_text()
source=runpy.run_path(str(shared/'prepare-nvram-commit-order.py'))['prepare'](source)
source=runpy.run_path(str(shared/'prepare-nvram-flash-readback.py'))['prepare'](source)
with tempfile.TemporaryDirectory(prefix='wr-readback-guard-') as directory:
    trunk=Path(directory);native=trunk/'linux-4.4.x/drivers/nvram/nvram_linux.c'
    header=native.parent/'wr-nvram-flash-wire.h';native.parent.mkdir(parents=True)
    native.write_text(source);header.write_bytes((here/'native-flash-wire.h').read_bytes())
    result=guard['verify'](trunk)
    assert result['verified'] and 'PREPARED 1\n' in guard['marker'](result)
    assert 'PREPARED 0\n' in guard['marker']({'verified':False})
    def refused():
        try:guard['verify'](trunk)
        except ValueError:return
        raise AssertionError('Modified or linked native readback accepted')
    for path in (native,header):
        original=path.read_bytes();path.write_bytes(original+b'\n');refused()
        path.write_bytes(original)
        backup=path.with_suffix('.backup');path.rename(backup);path.symlink_to(backup.name)
        refused();path.unlink();backup.rename(path)
        path.unlink();refused();path.write_bytes(original)
    assert guard['verify'](trunk)==result
print('PASS actual readback source guard: exact prepared code/wire match; changed/missing/symlink source/header refuse; capability zero defaults')
