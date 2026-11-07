#!/usr/bin/env python3
"""Stage WEXT RadioOn retirement admission on the reviewed candidate source."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('source', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
src = a.source.resolve(strict=True)
out = a.output.resolve()
if out.exists() or src == out or src in out.parents or out in src.parents:
    p.error('new separate output required')
name = 'common/cmm_cfg.c'
raw = (src / name).read_bytes()
digest = hashlib.sha256(raw).hexdigest()
s = raw.decode()
signature = 'INT\tSet_RadioOn_Proc('
begin = s.index(signature)
end = s.index('\n}', begin) + 2
body = s[begin:end]
if hashlib.sha256(body.encode()).hexdigest() != '0e9418a0b588f0021341cfa826d8630ba056139424a641ed1233cffeae49dffa':
    p.error('unreviewed RadioOn function predecessor')
anchor = '\tUCHAR radio;\n'
if body.count(anchor) != 1:
    p.error('changed RadioOn declaration')
gate = '''	UCHAR radio;
#if defined(MT7603) && defined(DMA_RESET_SUPPORT)
 ULONG wr_flags = 0;
 int wr_allowed;
 /* WEXT holds RTNL across this complete handler. Removal first retires
  * admission, then acquires RTNL before terminal work. Thus an admitted
  * pre-retirement call completes before that rendezvous; later calls refuse. */
 RTMP_IRQ_LOCK(&pAd->wr_iot_transition_lock, wr_flags);
 wr_allowed = !pAd->wr_iot_transition.retiring;
 RTMP_IRQ_UNLOCK(&pAd->wr_iot_transition_lock, wr_flags);
 if (!wr_allowed)
  return FALSE;
#endif
'''
body = body.replace(anchor, gate, 1)
s = s[:begin] + body + s[end:]
shutil.copytree(src, out)
(out / name).write_text(s, encoding='utf-8', newline='\n')
out.with_name(out.name + '-manifest.json').write_text(json.dumps({
    'input_sha256': digest,
    'output_sha256': hashlib.sha256((out / name).read_bytes()).hexdigest(),
    'scope': 'WEXT RadioOn ioctl admission; requires kernel RTNL dispatch and removal rendezvous',
    'full_composition_verified': False,
    'target_compiled': False,
    'runtime_verified': False,
    'production_installed': False,
}, indent=2) + '\n')
print('Staged RadioOn retirement gate; full composition and target verification pending')
