#!/usr/bin/env python3
"""Check RSSI kick presence, not physical-client behavior."""
import json
from pathlib import Path
import sys

trunk = Path(sys.argv[1]) / 'trunk'
romfs = trunk / 'romfs'
checks = {}
for radio, page in [('wl', 'Advanced_Wireless_Content.asp'), ('rt', 'Advanced_Wireless2g_Content.asp')]:
    page_text = (romfs / 'www' / page).read_text()
    for suffix in ['KickStaRssiLow', 'AssocReqRssiThres']:
        key = radio + '_' + suffix
        checks[key + '_web'] = ('name="' + key + '"') in page_text
        checks[key + '_rc'] = key.encode() in (romfs / 'sbin/rc').read_bytes()
        defaults = (trunk / 'user/shared/defaults.c').read_text()
        checks[key + '_default_off'] = ('{ "' + key + '", "0" }') in defaults
for module in ['mt76x2_ap.ko', 'mt76x3_ap.ko']:
    matches = list((romfs / 'lib/modules').rglob(module))
    checks[module + '_unique'] = len(matches) == 1
    if len(matches) == 1:
        blob = matches[0].read_bytes()
        checks[module + '_kick_command'] = b'KickStaRssiLow' in blob
        checks[module + '_assoc_command'] = b'AssocReqRssiThres' in blob
result = {'checks': checks, 'runtime_verified': False,
          'scope': 'image controls, compiled command strings and factory defaults only'}
Path('rssi-image-checks.json').write_text(json.dumps(result, indent=2) + '\n')
if not all(checks.values()):
    raise SystemExit('RSSI image checks failed: ' + ', '.join(k for k, v in checks.items() if not v))
print(json.dumps(result))
