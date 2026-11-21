#!/usr/bin/env python3
"""Stage IRQ-locked legacy/MT PS admission fences; UAPSD remains unbound."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
source=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or source==out or source in out.parents or out in source.parents:p.error('new separate output required')
receipt=json.loads(source.with_name(source.name+'-dequeue.json').read_text())
raw=(source/'common/cmm_data.c').read_bytes();ps=(source/'common/ps.c').read_bytes()
if hashlib.sha256(raw).hexdigest()!=receipt['output_sha256'] or receipt['production_installed'] is not False:p.error('dequeue receipt mismatch')
if hashlib.sha256(ps).hexdigest()!='8815abe01645e6010488902e7c09d23f4a9aad1df639edc18e5c8ab29099858c':p.error('unreviewed legacy PS input')
s=ps.decode().replace('\r\n','\n')
anchor='\t\t\tRTMP_IRQ_LOCK(&pAd->irq_lock /*&tr_entry->ps_queue_lock*/, IrqFlags);\n\t\t\tInsertTailQueue'
new='\t\t\tRTMP_IRQ_LOCK(&pAd->irq_lock /*&tr_entry->ps_queue_lock*/, IrqFlags);\n' +     '\t\t\tif (!tr_entry->enq_cap || tr_entry->ps_queue.Number >= MAX_PACKETS_IN_PS_QUEUE) {\n' +     '\t\t\t\tRTMP_IRQ_UNLOCK(&pAd->irq_lock /*&tr_entry->ps_queue_lock*/, IrqFlags);\n' +     '\t\t\t\tRELEASE_NDIS_PACKET(pAd, pPacket, NDIS_STATUS_FAILURE);\n' +     '\t\t\t\treturn NDIS_STATUS_FAILURE;\n\t\t\t}\n\t\t\tInsertTailQueue'
if s.count(anchor)!=1:p.error('PS insertion anchor changed')
s=s.replace(anchor,new,1)
c=raw.decode().replace('\r\n','\n')
anchor='\t\t\t\t\tif (tr_entry->ps_queue.Number >= MAX_PACKETS_IN_PS_QUEUE)'
if c.count(anchor)!=1:p.error('MT retrieve PS insertion changed')
c=c.replace(anchor,'\t\t\t\t\tif (!tr_entry->enq_cap || tr_entry->ps_queue.Number >= MAX_PACKETS_IN_PS_QUEUE)',1)
shutil.copytree(source,out)
(out/'common/ps.c').write_text(s,encoding='utf-8',newline='\n')
(out/'common/cmm_data.c').write_text(c,encoding='utf-8',newline='\n')
report={'changed_sha256':{n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['common/ps.c','common/cmm_data.c']},
 'uapsd_fence_bound':False,'writer_fence_bound':False,'production_installed':False,
 'target_compiled':False,'runtime_verified':False,'scope':'legacy/MT PS same-lock admission only'}
out.with_name(out.name+'-ps-fence.json').write_text(json.dumps(report,indent=2)+'\n')
print('Staged legacy/MT PS IRQ-locked admission; UAPSD/writer binding remains open')
