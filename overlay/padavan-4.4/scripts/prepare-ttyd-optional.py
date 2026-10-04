#!/usr/bin/env python3
"""Keep optional ttyd 1.7.7 login terminal writable when explicitly started."""
import sys
from pathlib import Path
path = Path(sys.argv[1]) / 'trunk/user/ttyd/ttyd.sh'
text = path.read_text()
old = 'start-stop-daemon -S -b -x ttyd -- -i br0 -p "$port"'
if text.count(old) != 1:
    raise SystemExit('Pinned ttyd startup anchor changed; no files written')
path.write_text(text.replace(old, old.replace('ttyd -- -i', 'ttyd -- -W -i')))
print('Optional ttyd login accepts input; existing LAN binding/login/runtime default preserved')
