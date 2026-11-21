#!/usr/bin/env python3
"""Stage normal-queue capability disable under irq_lock; not full peer retirement."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
source=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or source==out or source in out.parents or out in source.parents:p.error('new separate output required')
name='mgmt/mgmt_entrytb.c';raw=(source/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='d8c38bebce1b9b4612aceead5b9c2c9acf77a1e6c3bba07dcc06e977c06ae426':p.error('unreviewed TR reset source')
s=raw.decode().replace('\r\n','\n');start=s.index('VOID tr_tb_reset_entry(');end=s.index('VOID tr_tb_set_entry(',start);body=s[start:end]
old='\tINT qidx;';new=old+'\n\tULONG wr_iot_flags;'
if body.count(old)!=1:p.error('reset local anchor changed')
body=body.replace(old,new,1)
old='\ttr_entry->enq_cap = FALSE;\n\ttr_entry->deq_cap = FALSE;'
new='\t/* Existing caller owns MacTabLock; queue cleanup already uses irq_lock.\n\t * Publish the admission fence atomically with normal enqueue/dequeue. */\n\tRTMP_IRQ_LOCK(&pAd->irq_lock, wr_iot_flags);\n\tWRITE_ONCE(tr_entry->enq_cap, FALSE);\n\tWRITE_ONCE(tr_entry->deq_cap, FALSE);\n\tRTMP_IRQ_UNLOCK(&pAd->irq_lock, wr_iot_flags);'
if body.count(old)!=1:p.error('reset capability store changed')
body=body.replace(old,new,1);s=s[:start]+body+s[end:]
shutil.copytree(source,out);(out/name).write_text(s,encoding='utf-8',newline='\n')
out.with_name(out.name+'-writer.json').write_text(json.dumps({
 'input_sha256':hashlib.sha256(raw).hexdigest(),'output_sha256':hashlib.sha256((out/name).read_bytes()).hexdigest(),
 'reset_disable_irq_locked':True,'initialization_publication_reviewed':False,
 'uapsd_join_bound':False,'dma_rx_quiescence_proved':False,
 'target_compiled':False,'production_installed':False,'runtime_verified':False},indent=2)+'\n')
print('Staged IRQ-locked reset disable; initialization/UAPSD/DMA/RX remain open')
