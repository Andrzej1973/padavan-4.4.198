#!/usr/bin/env python3
"""Bind config-owner begin/abandon into outer init while retaining final refusal."""
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
        or 'mcu_config_timing' not in m or 'mcu_config_init_owner' in m
        or actual != m['merged_driver_sha256']):
    p.error('Expected unchanged timing-config candidate')

name = 'common/rtmp_init_inf.c'
text = (src / name).read_text()
start = text.index('int rt28xx_init(')
end = text.index('\nVOID RTMPDrvOpen(', start)
body = text[start:end]
guard = '#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'

def one(old, new):
    global body
    if body.count(old) != 1:
        p.error('Changed config-init owner anchor: ' + old)
    body = body.replace(old, new, 1)

one('\tNDIS_STATUS Status;', '''\tNDIS_STATUS Status;
'''+guard+'''
 struct wr_iot_mcu_boot_ticket wr_config_ticket;
 int wr_config_started=0;
#endif''')
outer_guard = '#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)'
outer = '''if (MCUSysInit(pAd) != NDIS_STATUS_SUCCESS)
\t\tgoto err6;
'''+outer_guard+'''
 /* Until a ROM/RX/ring epoch commit is bound, never publish boot success. */
 if(pAd->wr_iot_boot_active)goto err6;
#endif'''
replacement = '''if (MCUSysInit(pAd) != NDIS_STATUS_SUCCESS)
\t\tgoto err6;
'''+guard+'''
 if(pAd->wr_iot_boot_active){
  wr_config_ticket=pAd->wr_iot_boot_ticket;
  if(wr_iot_mcu_boot_config_begin(pAd,&wr_config_ticket)!=NDIS_STATUS_SUCCESS)goto err6;
  wr_config_started=1;
 }
#endif'''
one(outer, replacement)
one('\tDBGPRINT_S(("<==== rt28xx_init, Status=%x\\n", Status));', ''''''+guard+'''
 if(wr_config_started){
  if(wr_iot_mcu_boot_config_finish(pAd,&wr_config_ticket,1)!=NDIS_STATUS_SUCCESS)goto wr_config_err;
  wr_config_started=0;
  /* Normal command/data admission remains separately closed. */
  goto wr_config_err;
 }
#endif
\tDBGPRINT_S(("<==== rt28xx_init, Status=%x\\n", Status));''')
one('err6:\n', '''err6:
'''+guard+'''
 if(wr_config_started){
  (void)wr_iot_mcu_boot_config_finish(pAd,&wr_config_ticket,0);
  wr_config_started=0;
 }
#endif
''')

# The final return gate is too late for scan-time hardware admission.
# Keep every outer-init enable site behind the same unfinished-owner refusal.
for action in ('RTMP_IRQ_ENABLE(pAd);', 'RTMPEnableRxTx(pAd);',
               'APStartUp(pAd);', 'MlmeRadioOn(pAd);',
               'APOverlappingBSSScan(pAd);'):
    if action not in body:
        p.error('Missing startup admission site: ' + action)
    body = body.replace(action, guard + '''
 if(wr_config_started)goto wr_config_err;
#endif
 ''' + action)
one('\n#ifdef CONFIG_ATE\nerr9:', '\n'+guard+'\nwr_config_err:\n#endif\n#ifdef CONFIG_ATE\nerr9:')

(src / name).write_text(text[:start] + body + text[end:])
digest = hashlib.sha256((src / name).read_bytes()).hexdigest()
m['merged_driver_sha256'][name] = digest
m['candidate_driver_sha256'][name] = digest
m['mcu_config_init_owner'] = {
    'input_manifest_sha256': hashlib.sha256(raw).hexdigest(),
    'output_sha256': {name: digest},
    'outer_init_bound': True,
    'success_still_refused': True,
    'early_irq_rx_tx_refused': True,
    'early_overlap_scan_refused': True,
    'target_compiled': False,
    'runtime_verified': False,
}
mp.write_text(json.dumps(m, indent=2) + '\n')
