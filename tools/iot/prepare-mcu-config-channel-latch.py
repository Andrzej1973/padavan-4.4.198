#!/usr/bin/env python3
"""Keep private channel latch behind successful channel and power commands."""
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
        or 'mcu_config_edca_direct' not in m or 'mcu_config_channel_latch' in m
        or actual != m['merged_driver_sha256']):
    p.error('Expected unchanged isolated direct-EDCA candidate')
name = 'chips/mt7603.c'
text = (src / name).read_text()
start = text.index('static void mt7603_switch_channel(')
end = text.index('\n}\n', start) + 3
body = text[start:end]
anchor = '\n\n\tif (pAd->CommonCfg.BBPCurrentBW == BW_20)'
if body.count(anchor) != 1:
    p.error('Changed channel-switch entry')
guard = '#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
private = '''
'''+guard+'''
 if(pAd->wr_iot_boot_active){
  if(pAd->wr_iot_boot_failed)return;
  if(CmdChannelSwitch(pAd,
      pAd->CommonCfg.BBPCurrentBW==BW_20?channel:pAd->CommonCfg.Channel,
      channel,pAd->CommonCfg.BBPCurrentBW,
      pAd->CommonCfg.TxStream,pAd->CommonCfg.RxStream)!=NDIS_STATUS_SUCCESS){
   (void)wr_iot_mcu_config_fail(pAd);
   return;
  }
  if(pAd->wr_iot_boot_failed)return;
  CmdSetTxPowerCtrl(pAd,channel);
  if(pAd->wr_iot_boot_failed)return;
  pAd->LatchRfRegs.Channel=channel;
  return;
 }
#endif
'''
body = body.replace(anchor, private + anchor, 1)
(src / name).write_text(text[:start] + body + text[end:])
digest = hashlib.sha256((src / name).read_bytes()).hexdigest()
for key in ('merged_driver_sha256', 'candidate_driver_sha256'):
    m[key][name] = digest
m['mcu_config_channel_latch'] = {
    'input_manifest_sha256': hashlib.sha256(raw).hexdigest(),
    'output_sha256': {name: digest}, 'production_installed': False,
    'target_compiled': False, 'runtime_verified': False}
mp.write_text(json.dumps(m, indent=2) + '\n')
