#!/usr/bin/env python3
"""Stage UAPSD same-lock admission; retirement writer/join is separate."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
source=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or source==out or source in out.parents or out in source.parents:p.error('new separate output required')
name='common/uapsd.c';raw=(source/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='d8cf132b185d1f6eec569674e7d6651cfe156879f3870f864907322622a31ef5':p.error('unreviewed UAPSD source')
s=raw.decode().replace('\r\n','\n');old='\t\tUAPSD_SEM_LOCK(&pAd->UAPSDEOSPLock, flags);\n\t\tif (bFromHead)'
new='\t\tUAPSD_SEM_LOCK(&pAd->UAPSDEOSPLock, flags);\n\t\t/* Admission and capacity are checked at insertion, not before the lock.\n\t\t * Retirement must fence normal producers and join this lock separately;\n\t\t * do not nest irq_lock inside the UAPSD lock. */\n\t\tif (pEntry->wcid >= MAX_LEN_OF_TR_TABLE ||\n\t\t    !READ_ONCE(pAd->MacTab.tr_entry[pEntry->wcid].enq_cap) ||\n\t\t    pQueUapsd->Number >= MAX_PACKETS_IN_UAPSD_QUEUE) {\n\t\t\tUAPSD_SEM_UNLOCK(&pAd->UAPSDEOSPLock, flags);\n\t\t\tRELEASE_NDIS_PACKET(pAd, pPacket, NDIS_STATUS_FAILURE);\n\t\t\treturn;\n\t\t}\n\t\tif (bFromHead)'
if s.count(old)!=1:p.error('UAPSD insertion anchor changed')
s=s.replace(old,new,1);shutil.copytree(source,out)
(out/name).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-uapsd.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashlib.sha256((out/name).read_bytes()).hexdigest(),
 'writer_join_bound':False,'producer_fences_complete':False,
 'target_compiled':False,'production_installed':False,'runtime_verified':False,
 'scope':'UAPSD insertion admission only; no nested IRQ lock added'},indent=2)+'\n')
print('Staged UAPSD admission; writer/join and runtime remain unproven')
