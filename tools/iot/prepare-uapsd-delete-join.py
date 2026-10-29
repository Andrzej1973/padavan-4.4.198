#!/usr/bin/env python3
"""Stage deletion-only UAPSD queue join; no full lifetime/target acceptance."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
source=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or source==out or source in out.parents or out in source.parents:p.error('new separate output required')
pins={'mgmt/mgmt_entrytb.c': '3b274ed3742122b2323752702999c0ceb3f914a96211d8b38b4ec8aad636b926', 'common/uapsd.c': '5dba4f9f1c31dfd1fd81bf42adf7ccd92a7df1975919f022ee083e61af74aa78', 'include/uapsd.h': 'a3ffd5fbc1769260e63eb68afd051bbf9c4cd53921325b3019478453b5e0c9ad'}
for name,sha in pins.items():
 if hashlib.sha256((source/name).read_bytes()).hexdigest()!=sha:p.error('unreviewed delete-join input: '+name)
here=Path(__file__).resolve().parent
name='mgmt/mgmt_entrytb.c';s=(source/name).read_text();start=s.index('BOOLEAN MacTableDeleteEntry(');body=s[start:]
anchor='\t\tif (MAC_ADDR_EQUAL(pEntry->Addr, pAddr))\n\t\t{'
admission='\n\t\t\t/* Deletion-only join; caller owns MacTabLock and verified address. */\n\t\t\t{\n\t\t\t\tULONG wr_iot_flags;\n\t\t\t\tRTMP_IRQ_LOCK(&pAd->irq_lock, wr_iot_flags);\n\t\t\t\tWRITE_ONCE(tr_entry->enq_cap, FALSE);\n\t\t\t\tWRITE_ONCE(tr_entry->deq_cap, FALSE);\n\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->irq_lock, wr_iot_flags);\n#ifdef UAPSD_SUPPORT\n\t\t\t\tif (wr_iot_uapsd_retire_queues(pAd, pEntry) != NDIS_STATUS_SUCCESS) {\n\t\t\t\t\tNdisReleaseSpinLock(&pAd->MacTabLock);\n\t\t\t\t\treturn FALSE; /* retain disabled entry; recovery not implemented */\n\t\t\t\t}\n#endif\n\t\t\t}\n\t\t\t/* End deletion-only queue join. */'
if body.count(anchor)!=1:p.error('address-verified delete anchor changed')
body=body.replace(anchor,anchor+admission,1)
# Preserve unrelated PS-transition macro callers in other translation units.
if body.count('UAPSD_MR_ENTRY_RESET(pAd, pEntry);')!=2:p.error('delete reset call count changed')
body=body.replace('UAPSD_MR_ENTRY_RESET(pAd, pEntry);','/* Queues/EOSP retired at verified deletion admission above. */')
changed={name:s[:start]+body}
name='common/uapsd.c';s=(source/name).read_text();anchor='VOID UAPSD_Init(RTMP_ADAPTER *pAd)'
if s.count(anchor)!=1:p.error('UAPSD helper insertion changed')
changed[name]=s.replace(anchor,'#include "wr-iot-uapsd-retire-queues.inc"\n\n'+anchor,1)
name='include/uapsd.h';s=(source/name).read_text();changed[name]=s+'\nINT wr_iot_uapsd_retire_queues(RTMP_ADAPTER *pAd, MAC_TABLE_ENTRY *entry);\n'
shutil.copytree(source,out)
for n,text in changed.items():(out/n).write_text(text,encoding='utf-8',newline='\n')
shutil.copyfile(here/'uapsd-retire-queues.inc',out/'include/wr-iot-uapsd-retire-queues.inc')
out.with_name(out.name+'-delete-join.json').write_text(json.dumps({
 'input_sha256':pins,'output_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in [*changed, 'include/wr-iot-uapsd-retire-queues.inc']},
 'scope':'deletion-only source join; early failure retains disabled entry without recovery owner',
 'target_compiled':False,'production_installed':False,'runtime_verified':False,
 'full_callback_lifetime_proved':False,'initialization_reuse_proved':False},indent=2)+'\n')
print('Staged deletion-only UAPSD join; recovery/reuse/lifetime acceptance open')
