#!/usr/bin/env python3
"""Stage reserved IoT BSS snapshot admission in isolated driver, retaining all ownership gates."""
import argparse,hashlib,json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path)
p.add_argument('--install-isolated',action='store_true',required=True);a=p.parse_args()
src=a.source.resolve();mp=Path(str(src)+'.manifest.json');raw=mp.read_bytes();m=json.loads(raw)
actual={str(f.relative_to(src)):hashlib.sha256(f.read_bytes()).hexdigest() for f in src.rglob('*') if f.is_file()}
if m.get('production_installed') is not False or m.get('target_compiled') is not False or actual!=m['merged_driver_sha256'] or 'mcu_config_channel_scan' not in m or 'precreated_bss_admission' in m:p.error('Expected unchanged isolated channel-scan candidate')
guard='#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)'
changes={}
for name,anchor,injection in [
 ('ap/ap_assoc.c','\twdev = &pMbss->wdev;\n\ttr_entry = &pAd->MacTab.tr_entry[pEntry->wcid];',
  '\twdev = &pMbss->wdev;\n'+guard+'\n if(!wr_iot_precreated_bss_admitted(pAd,pEntry->func_tb_idx))goto LabelOK;\n#endif\n\ttr_entry = &pAd->MacTab.tr_entry[pEntry->wcid];'),
 ('ap/ap_data.c','\tpEntry = PACInquiry(pAd, pRxBlk->wcid);',
  '\tpEntry = PACInquiry(pAd, pRxBlk->wcid);\n'+guard+'\n if(pEntry&&IS_ENTRY_CLIENT(pEntry)&&\n    !wr_iot_precreated_bss_admitted(pAd,pEntry->func_tb_idx))return FALSE;\n#endif')]:
 s=(src/name).read_text();inc='#include "rt_config.h"'
 if s.count(inc)!=1 or s.count(anchor)!=1:p.error('Changed admission anchor '+name)
 s=s.replace(inc,inc+'\n'+guard+'\n#include "precreated-bss-admission.h"\n#include "precreated-loaded-config.h"\n#include "precreated-key-match.h"\n#endif',1).replace(anchor,injection,1);changes[name]=s
changes['include/precreated-bss-admission.h']=Path(__file__).with_name('precreated-bss-admission.h').read_text()
changes['include/precreated-loaded-config.h']=Path(__file__).with_name('precreated-loaded-config.h').read_text()
changes['include/precreated-key-match.h']=Path(__file__).with_name('precreated-key-match.h').read_text()
for name,s in changes.items():(src/name).write_text(s)
hashes={name:hashlib.sha256((src/name).read_bytes()).hexdigest() for name in changes}
m['merged_driver_sha256'].update(hashes);m['candidate_driver_sha256'].update(hashes)
m['precreated_bss_admission']={'input_manifest_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashes,'scope':'third BSS association/data snapshot rejection, existing lifetime/transition gates retained','target_compiled':False,'runtime_verified':False}
mp.write_text(json.dumps(m,indent=2)+'\n')
