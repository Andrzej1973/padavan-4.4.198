#!/usr/bin/env python3
"""Stage per-WCID dequeue fences in a separate full source tree, not production."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();source=a.source.resolve(strict=True);out=a.output.resolve()
if out.exists() or source==out or source in out.parents or out in source.parents:p.error('new separate output required')
name='common/cmm_data.c';raw=(source/name).read_bytes()
if hashlib.sha256(raw).hexdigest()!='8453ace194ac21304a4a4021c51c5caf2f4fb2c00db2fab87216ba5070123a03':p.error('unreviewed queue source')
s=raw.decode('utf-8').replace('\r\n','\n')
def one(old,new):
 global s
 if s.count(old)!=1:p.error('dequeue anchor changed: '+old[:50])
 s=s.replace(old,new,1)
one('#include "rt_config.h"','#include "rt_config.h"\n#include "wcid-fifo-retirement.h"')
one('\t\tdeq_wcid = info->target_wcid;',
    '\t\tdeq_wcid = info->target_wcid;\n'
    '\t\tif (!pAd->MacTab.tr_entry[deq_wcid].deq_cap) {\n'
    '\t\t\tinfo->status = NDIS_STATUS_FAILURE;\n\t\t\tgoto done;\n\t\t}')
old='\t\tfifo_swq = &pAd->tx_swq[deq_qid];\n\t\tdeq_wcid = fifo_swq->swq[fifo_swq->deqIdx];'
new=r"""
        fifo_swq = &pAd->tx_swq[deq_qid];
        {
            unsigned int scan, removed;
            int available;
            /* Caller holds irq_lock through request/gather/hard_tx/report.
             * Do not compact physical indices retained by packet metadata. */
            for (scan = 0; scan < TX_SWQ_FIFO_LEN; scan++) {
                available = wr_iot_wcid_fifo_head(fifo_swq->swq,
                    TX_SWQ_FIFO_LEN, &fifo_swq->deqIdx, fifo_swq->enqIdx,
                    &deq_wcid);
                if (available < 0) {info->status=NDIS_STATUS_FAILURE;goto done;}
                if (!available) break;
                if (deq_wcid >= MAX_LEN_OF_TR_TABLE) {
                    info->status=NDIS_STATUS_FAILURE;goto done;
                }
                if (pAd->MacTab.tr_entry[deq_wcid].deq_cap) break;
                if (!wr_iot_wcid_fifo_retire(fifo_swq->swq,
                    TX_SWQ_FIFO_LEN, &fifo_swq->deqIdx, fifo_swq->enqIdx,
                    deq_wcid, &removed)) {
                    info->status=NDIS_STATUS_FAILURE;goto done;
                }
            }
            if (scan == TX_SWQ_FIFO_LEN) {
                info->status=NDIS_STATUS_FAILURE;goto done;
            }
        }
"""
one(old,new.strip('\n'))
helper=Path(__file__).with_name('wcid-fifo-retirement.h').read_bytes()
if (source/'include/wcid-fifo-retirement.h').exists():p.error('helper already present')
shutil.copytree(source,out);(out/name).write_text(s,encoding='utf-8',newline='\n')
(out/'include/wcid-fifo-retirement.h').write_bytes(helper)
report={'changed_file':name,'input_sha256':hashlib.sha256(raw).hexdigest(),
 'output_sha256':hashlib.sha256((out/name).read_bytes()).hexdigest(),
 'helper_sha256':hashlib.sha256(helper).hexdigest(),'production_installed':False,
 'target_compiled':False,'runtime_verified':False,'producer_fences_complete':False,
 'dma_rx_quiescence_proved':False,'scope':'dequeue source binding only; mode/accounting and target checks pending'}
out.with_name(out.name+'-dequeue.json').write_text(json.dumps(report,indent=2)+'\n')
print('Staged isolated WCID dequeue fence; producer/DMA/RX acceptance remains open')
