#!/usr/bin/env python3
"""Keep MT7603E Band Steering compatible with the existing WPS-disabled build."""
import argparse
import hashlib
import json
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('source', type=Path)
root = p.parse_args().source
path = root / 'trunk/linux-4.4.x/drivers/net/wireless/mediatek/mt76x3/ap/ap_band_steering.c'
before = path.read_bytes()
if hashlib.sha256(before).hexdigest() != 'f8de06a8afc5de33904f9935ee4ab4e6bb4a781bd9643a97c1fbc4a90b20b0f5':
    raise ValueError('Expected grant-prepared modern driver; no files written')
s = before.decode()
start_marker = '/* WPS_BandSteering Support */\n\t{\n\t\tPWSC_CTRL pWscControl;'
end_marker = '\n\tif (table->BndStrgMode == POST_CONNECTION_STEERING)'
assignment = '\t\tcli_assoc->bWpsAssoc = ie_list->bWscCapable;'
if s.count(start_marker) != 1 or s.count(assignment) != 1:
    raise ValueError('WPS integration anchors changed; no files written')
start = s.index(start_marker)
end = s.index(end_marker, start)
block = s[start:end]
if not block.rstrip().endswith('}'):
    raise ValueError('Unexpected WPS block boundary; no files written')
s = s[:start] + '#ifdef WSC_AP_SUPPORT\n' + block + '#endif /* WSC_AP_SUPPORT */\n' + s[end:]
s = s.replace(assignment, '#ifdef WSC_AP_SUPPORT\n' + assignment +
    '\n#else\n\t\tcli_assoc->bWpsAssoc = FALSE;\n#endif /* WSC_AP_SUPPORT */')
with path.open('w', encoding='utf-8', newline='\n') as out:
    out.write(s)
report = {'runtime_verified': False, 'enables_wps': False,
          'before_sha256': hashlib.sha256(before).hexdigest(),
          'after_sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
(root / 'band-steering-wps-preparation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))

