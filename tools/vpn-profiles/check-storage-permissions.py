#!/usr/bin/env python3
"""Reproduce file-only archive mode loss; exercise actual shell repair."""
import ast
import io
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

source = Path(__file__).with_name('prepare-storage-permissions.py')
tree = ast.parse(source.read_text())
helper = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == 'HELPER' for t in n.targets))
with tempfile.TemporaryDirectory(prefix='wrvpn-storage-') as temporary:
    root = Path(temporary)
    archive = root / 'storage.tar'
    with tarfile.open(archive, 'w') as tar:
        entry = tarfile.TarInfo('wrvpn/1');entry.size = 7;entry.mode = 0o600
        tar.addfile(entry, io.BytesIO(b'fixture'))
    restored = root / 'restored';restored.mkdir()
    subprocess.run(['tar', 'xf', str(archive), '-C', str(restored)], check=True,
                   preexec_fn=lambda: os.umask(0o022))
    profile = restored / 'wrvpn'
    assert profile.stat().st_mode & 0o777 == 0o755
    script = root / 'repair.sh';script.write_text(helper + '\nfunc_wrvpn_private "$1"\n')
    def run(path, success=True):
        r = subprocess.run(['/bin/sh', str(script), str(path)], capture_output=True, timeout=5)
        assert (r.returncode == 0) == success and not r.stdout, (r.returncode, r.stderr)
    run(restored)
    assert profile.stat().st_mode & 0o777 == 0o700
    assert (profile / '1').read_bytes() == b'fixture'
    assert (profile / '1').stat().st_mode & 0o777 == 0o600
    run(restored) # Idempotent and no record rewrites.
    absent = root / 'absent';absent.mkdir();run(absent);assert not (absent / 'wrvpn').exists()
    linked = root / 'linked';linked.mkdir();(linked / 'wrvpn').symlink_to(profile)
    run(linked, False)
    bad = root / 'bad';bad.mkdir();(bad / 'wrvpn').write_text('not a directory');run(bad, False)
print('PASS file-only storage archive reproduction: 0755 rejected shape repaired to 0700; records/modes preserved; symlink/non-directory refused; no flash writes')
