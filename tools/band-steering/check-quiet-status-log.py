"""Require only the periodic status log level to change in actual source."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
a = p.parse_args()
relative = Path('trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_band_steering.c')
original = (a.source / relative).read_text(encoding='utf-8')
lines = [line for line in original.splitlines(keepends=True)
         if 'STATUS QUERY ON' in line and 'BND_STRG_MTWF_LOG(' in line]
assert len(lines) == 1 and 'DBG_LVL_OFF' in lines[0], 'Pinned periodic log changed'
expected = original.replace(lines[0], lines[0].replace('DBG_LVL_OFF', 'DBG_LVL_TRACE', 1), 1)
root = Path.cwd() / ('quiet-log-check-' + uuid.uuid4().hex)
root.mkdir()
try:
    target = root / relative
    target.parent.mkdir(parents=True)
    script = Path(__file__).with_name('prepare-quiet-status-log.py')
    def run(source, success):
        target.write_text(source, encoding='utf-8')
        result = subprocess.run([sys.executable, str(script), str(root)], capture_output=True, text=True)
        assert (result.returncode == 0) == success, result.stderr
        return target.read_text(encoding='utf-8')
    assert run(original, True) == expected, 'Protocol or unrelated code changed'
    assert run(expected, False) == expected, 'Repeated preparation mutated source'
    changed = original.replace(lines[0], lines[0].replace('DBG_LVL_OFF', 'DBG_LVL_WARN', 1), 1)
    assert run(changed, False) == changed
    duplicate = original + lines[0]
    assert run(duplicate, False) == duplicate
finally:
    assert root.resolve().parent == Path.cwd().resolve()
    shutil.rmtree(root)
print('PASS periodic steering log changes OFF to TRACE only; protocol source preserved; repeated/changed/duplicate anchors rejected')
