#!/usr/bin/env python3
"""Verify observer preparation leaves the homepage clean and unchanged."""
import shutil
import subprocess
import sys
import uuid
from pathlib import Path

local = Path(__file__).resolve().parent
relative = Path('trunk/user/www/n56u_ribbon_fixed/index.asp')
root = Path.cwd() / ('homepage-check-' + uuid.uuid4().hex)
assert root.resolve().parent == Path.cwd().resolve()
source = root / relative
source.parent.mkdir(parents=True)
original = ('<html><head></head><body>\n'
            '                <!--Body content-->\n'
            '<iframe id="statusframe"></iframe></body></html>\n')
source.write_text(original, encoding='utf-8')
try:
    for _ in range(2):
        subprocess.run([sys.executable, str(local / 'prepare-ui.py'), str(root)], check=True)
        assert source.read_text(encoding='utf-8') == original
    for marker in ('wr-observation-launcher', 'wr-connected-devices',
                   'wr-roaming-history', 'wr-rssi-history', 'wr_view=',
                   '/wr-device-'):
        source.write_text(original.replace('</body>', marker + '</body>'), encoding='utf-8')
        before = source.read_bytes()
        result = subprocess.run([sys.executable, str(local / 'prepare-ui.py'), str(root)],
                                capture_output=True)
        assert result.returncode != 0 and source.read_bytes() == before, marker
finally:
    assert root.resolve().parent == Path.cwd().resolve()
    shutil.rmtree(root)
print('PASS homepage remains unchanged and observer panels/links are rejected')
