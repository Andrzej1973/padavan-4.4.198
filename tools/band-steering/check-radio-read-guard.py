#!/usr/bin/env python3
"""Exercise preparation drift rejection before mutating the real source tree."""
import argparse
from pathlib import Path
import re
import subprocess
import sys

p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
args = p.parse_args()
original = (args.source / 'trunk/user/rc/net_wifi.c').read_bytes()
text = original.decode('utf-8').replace('\r\n', '\n')
script = Path(__file__).with_name('prepare-radio-snapshot.py').resolve()
cases = [('valid', text, True)]
for api in ('nvram_wlan_get', 'nvram_wlan_get_int', 'nvram_get_int'):
    # A comment still changes the audited textual sites and requires review.
    added = text.replace('#include "rc.h"\n',
                         '#include "rc.h"\n/* '+api+'(0) */\n', 1)
    removed, count = re.subn(r'\b'+api+r'(?=\s*\()',
                            'changed_read_api', text, count=1)
    if count != 1 or added == text:
        raise ValueError('Guard fixture source no longer matches '+api)
    cases += [(api+'-added', added, False), (api+'-removed', removed, False)]
args.output.mkdir(parents=True, exist_ok=False)
for name, candidate, success in cases:
    root = args.output / name
    path = root / 'trunk/user/rc/net_wifi.c'
    path.parent.mkdir(parents=True)
    before = candidate.encode('utf-8')
    path.write_bytes(before)
    result = subprocess.run([sys.executable, str(script), str(root)],
                            capture_output=True, text=True)
    if success:
        if result.returncode or 'wr_radio_snapshot' not in path.read_text():
            raise AssertionError(name+': '+result.stderr)
    elif (result.returncode == 0 or
          'Audited radio read counts changed' not in result.stderr or
          path.read_bytes() != before):
        raise AssertionError(name+': rejection or unchanged-file proof failed')
    print(name+': PASS')
if (args.source / 'trunk/user/rc/net_wifi.c').read_bytes() != original:
    raise AssertionError('Guard fixtures modified the real source')
