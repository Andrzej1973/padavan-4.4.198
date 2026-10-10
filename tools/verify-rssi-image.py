#!/usr/bin/env python3
"""Check RSSI kick presence, not physical-client behavior."""
import json,hashlib,subprocess,argparse
from pathlib import Path
import sys

parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('--nm',required=True);args=parser.parse_args()
trunk = args.source / 'trunk'
romfs = trunk / 'romfs'
checks = {}
modules = {}
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
        symbols=subprocess.run([args.nm,str(matches[0])],check=True,capture_output=True,text=True).stdout
        checks[module + '_observer_symbol'] = any(line.split()[-1:] == ['wr_rssi_delete_entry'] for line in symbols.splitlines())
        checks[module + '_elf_mips'] = len(blob)>20 and blob[:5]==b'\x7fELF\x01' and blob[5]==1 and int.from_bytes(blob[18:20],'little')==8
        modules[module]={'sha256':hashlib.sha256(blob).hexdigest(),'bytes':len(blob),'path':str(matches[0].relative_to(romfs))}
        checks[module + '_kick_command'] = b'KickStaRssiLow' in blob
        checks[module + '_assoc_command'] = b'AssocReqRssiThres' in blob
result = {'checks': checks, 'modules': modules, 'runtime_verified': False,
          'scope': 'image controls, packaged MIPS observer modules, compiled command strings and factory defaults only'}
Path('rssi-image-checks.json').write_text(json.dumps(result, indent=2) + '\n')
if not all(checks.values()):
    raise SystemExit('RSSI image checks failed: ' + ', '.join(k for k, v in checks.items() if not v))
print(json.dumps(result))
