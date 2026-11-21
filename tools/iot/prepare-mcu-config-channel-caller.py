#!/usr/bin/env python3
"""Stop outer MT channel side effects after private configuration failure."""
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
        or 'mcu_config_channel_latch' not in m or 'mcu_config_channel_caller' in m
        or actual != m['merged_driver_sha256']):
    p.error('Expected unchanged isolated channel-latch candidate')
name = 'hw_ctrl/cmm_asic_mt.c'
text = (src / name).read_text()
start = text.index('VOID AsicSwitchChannel(')
end = text.index('\n}\n', start) + 3
body = text[start:end]
guard = '#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
anchor = '\tUCHAR bw;'
if body.count(anchor) != 1:
    p.error('Changed outer channel entry')
body = body.replace(anchor, anchor + '\n' + guard + '''
 if(pAd->wr_iot_boot_active){
  if(pAd->wr_iot_boot_failed)return;
  if(!pAd->chipOps.ChipSwitchChannel){
   (void)wr_iot_mcu_config_fail(pAd);
   return;
  }
 }
#endif''', 1)
anchor = '\n#ifdef MT_MAC\n\t// TODO: shiang-7603'
if body.count(anchor) != 1:
    p.error('Changed outer channel MMIO boundary')
body = body.replace(anchor, '\n' + guard + '''
 if(pAd->wr_iot_boot_active&&pAd->wr_iot_boot_failed)return;
#endif
''' + anchor, 1)
(src / name).write_text(text[:start] + body + text[end:])
digest = hashlib.sha256((src / name).read_bytes()).hexdigest()
for key in ('merged_driver_sha256', 'candidate_driver_sha256'):
    m[key][name] = digest
m['mcu_config_channel_caller'] = {
    'input_manifest_sha256': hashlib.sha256(raw).hexdigest(),
    'output_sha256': {name: digest}, 'production_installed': False,
    'target_compiled': False, 'runtime_verified': False}
mp.write_text(json.dumps(m, indent=2) + '\n')
