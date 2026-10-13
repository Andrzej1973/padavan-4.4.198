#!/usr/bin/env python3
"""Execute the collector's real AWK filter without accessing a router."""
from pathlib import Path
import re
import shutil
import subprocess

source=Path(__file__).with_name('collect-wr1200js-readiness.sh').read_text(encoding='utf-8')
match=re.search(r"    awk '([\s\S]+?)' \"\$dns_custom\"",source)
assert match,'Collector AWK anchor changed'
assert 'command -v' not in source
awk=shutil.which('awk')
if not awk:
    candidate=Path('C:/Program Files/Git/usr/bin/awk.exe')
    if candidate.is_file():awk=str(candidate)
if not awk:raise SystemExit('AWK required to execute the real collector filter')
data='\n'.join([
    '# no-resolv',
    ' # server=127.0.0.1#65053',
    'no-resolv',
    '  server=127.0.0.1#5453',
    'server=127.0.0.1#65053 # private annotation',
    'server=/private.example/127.0.0.1#65053',
    'server=127.0.0.1#650530',
    'no-resolver',
    'server=1.1.1.1',
    'no-resolv # private annotation',
])+'\n'
result=subprocess.run([awk,match[1]],input=data,capture_output=True,text=True,timeout=5,check=True)
assert result.stdout.splitlines()==[
    'line 3: no-resolv',
    'line 4: global local DNS port 5453',
    'line 5: global local DNS port 65053',
    'line 10: no-resolv',
],result.stdout
assert 'private' not in result.stdout
print('PASS actual readiness DNS filter: comments ignored, exact ports, no domain/annotation output')
