#!/usr/bin/env python3
"""Stop private automatic channel selection after MCU configuration refusal."""
import argparse
import hashlib
import json
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('--install-isolated', action='store_true', required=True)
a = p.parse_args()
src = a.source.resolve()
mp = Path(str(src) + '.manifest.json')
raw = mp.read_bytes()
m = json.loads(raw)
actual = {str(f.relative_to(src)): hashlib.sha256(f.read_bytes()).hexdigest()
          for f in src.rglob('*') if f.is_file()}
if (m.get('production_installed') is not False or m.get('target_compiled') is not False
        or 'mcu_config_channel_caller' not in m or 'mcu_config_channel_scan' in m
        or actual != m['merged_driver_sha256']):
    p.error('Expected unchanged isolated channel-caller candidate')
name = 'ap/ap_autoChSel.c'
text = (src / name).read_text()
start = text.index('UCHAR APAutoSelectChannel(')
end = text.index('\n}\n', start) + 3
body = text[start:end]
guard = '''
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(pAd->wr_iot_boot_active&&pAd->wr_iot_boot_failed)return 0;
#endif
'''
for anchor in ('\tAPAutoChannelInit(pAd);',
               '\t\t\tAsicSwitchChannel(pAd, pAd->ChannelList[i].Channel, TRUE);'):
    if body.count(anchor) != 1:
        p.error('Changed automatic-channel anchor: ' + anchor)
    # The entry guard precedes initialization; the second follows the switch.
    body = body.replace(anchor, guard + anchor if 'Init' in anchor
                        else anchor + guard, 1)
(src / name).write_text(text[:start] + body + text[end:])
digest = hashlib.sha256((src / name).read_bytes()).hexdigest()
for key in ('merged_driver_sha256', 'candidate_driver_sha256'):
    m[key][name] = digest
m['mcu_config_channel_scan'] = {
    'input_manifest_sha256': hashlib.sha256(raw).hexdigest(),
    'output_sha256': {name: digest}, 'production_installed': False,
    'target_compiled': False, 'runtime_verified': False}
mp.write_text(json.dumps(m, indent=2) + '\n')
