"""Exercise exact generated diagnostic with native wrapped read syscalls."""
import argparse
import json
import os
from pathlib import Path
import subprocess

p = argparse.ArgumentParser()
p.add_argument('generated', type=Path)
a = p.parse_args()
local = Path(__file__).resolve().parent
source = a.generated.with_name('radio-diagnostic-test.c')
binary = a.generated.with_name('radio-diagnostic-test')
source.write_text(a.generated.read_text() + '\n' +
                  (local / 'radio-diagnostic-test-wrap.inc').read_text(), encoding='utf-8')
subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror',
                '-I'+str(local), str(source), '-Wl,--wrap=socket,--wrap=ioctl,--wrap=close',
                '-o', str(binary)], check=True)
for mode in ('success', 'short', 'error'):
    run = subprocess.run([str(binary.resolve())], env={**os.environ, 'WR_DIAGNOSTIC_TEST_MODE': mode},
                         capture_output=True, text=True, timeout=5)
    assert run.returncode == (0 if mode == 'success' else 1), run.stderr
    rows = [json.loads(line) for line in run.stdout.splitlines()]
    assert len(rows) == 2
    for band, row in enumerate(rows):
        assert set(row) == {'radio', 'ioctl_result', 'errno', 'returned_bytes', 'decode_valid', 'records'}
        assert row['radio'] == band and row['records'] == 0
        assert row['decode_valid'] == (mode == 'success')
        assert (row['errno'] > 0) == (mode == 'error')
        assert (row['ioctl_result'] < 0) == (mode == 'error')
        if mode == 'short':
            assert row['returned_bytes'] == 0
print('PASS diagnostic uses fixed read queries and reports valid, short and failed responses without identifiers; native mocks only')
