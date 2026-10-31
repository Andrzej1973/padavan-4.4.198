#!/usr/bin/env python3
"""Extract vendor per-WCID queue cleanup; host selection checks, not drain proof."""
import argparse
import hashlib
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args()
if a.output.exists():p.error('new output required')
source=(a.source/'common/cmm_data.c').read_text(encoding='utf-8')
start='INT rtmp_tx_swq_exit(RTMP_ADAPTER *pAd, UCHAR wcid)'
if source.count(start)!=1:p.error('ambiguous queue cleanup')
pos=source.index(start);brace=source.index('{',pos);depth=1;end=brace+1
while depth:
    depth+=(source[end]=='{')-(source[end]=='}');end+=1
body=source[pos:end]
if any(body.count(x)!=1 for x in ['wcid_start = wcid_end = wcid;',
 'pQueue = &tr_entry->tx_queue[ring_idx];','pQueue = &tr_entry->ps_queue;']):
    p.error('queue selector shape changed')
PREFIX='#include <assert.h>\n#include <stddef.h>\n#define WMM_QUE_NUM 2\n#define MAX_LEN_OF_TR_TABLE 3\n#define WCID_ALL 255\n#define TRUE 1\n#define FALSE 0\n#define RT_DEBUG_OFF 0\n#define DBGPRINT(level,args) do{(void)(level);}while(0)\ntypedef unsigned char UCHAR;typedef int INT;typedef unsigned long ULONG;\ntypedef struct packet {struct packet *next;int owner;} QUEUE_ENTRY;\ntypedef struct {QUEUE_ENTRY *Head;unsigned int Number;} QUEUE_HEADER;\ntypedef QUEUE_ENTRY *PNDIS_PACKET;\ntypedef struct {int none;QUEUE_HEADER tx_queue[2],ps_queue;} STA_TR_ENTRY;\ntypedef struct {int irq_lock;struct {STA_TR_ENTRY tr_entry[3];} MacTab; UCHAR fifo_tokens[4];} RTMP_ADAPTER;\nstatic int lock,freed[3];\n#define IS_ENTRY_NONE(e) ((e)->none)\n#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!lock);lock=1;}while(0)\n#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(lock);lock=0;}while(0)\nstatic QUEUE_ENTRY *remove_head(QUEUE_HEADER *q){QUEUE_ENTRY *x=q->Head;assert(lock&&x);q->Head=x->next;q->Number--;return x;}\n#define RemoveHeadQueue(q) remove_head(q)\n#define TR_ENQ_COUNT_DEC(e) do{(void)(e);}while(0)\n#define QUEUE_ENTRY_TO_PACKET(e) (e)\n#define NDIS_STATUS_FAILURE -1\n#define RELEASE_NDIS_PACKET(ad,p,status) do{(void)(ad);(void)(status);assert(lock);freed[(p)->owner]++;}while(0)\n'
SUFFIX='\nint main(void){RTMP_ADAPTER ad={0};QUEUE_ENTRY packets[3][3];int i,j;\nfor(i=0;i<3;i++)for(j=0;j<3;j++){packets[i][j]=(QUEUE_ENTRY){NULL,i};QUEUE_HEADER *q=j==2?&ad.MacTab.tr_entry[i].ps_queue:&ad.MacTab.tr_entry[i].tx_queue[j];q->Head=&packets[i][j];q->Number=1;}\nad.fifo_tokens[0]=1;ad.fifo_tokens[1]=2;ad.fifo_tokens[2]=1;\nassert(rtmp_tx_swq_exit(&ad,1)==TRUE);assert(freed[1]==3&&!freed[0]&&!freed[2]&&!lock);\nassert(ad.MacTab.tr_entry[0].tx_queue[0].Head&&ad.MacTab.tr_entry[2].ps_queue.Head);\n/* Known cleanup scope gap: global WCID scheduling tokens remain. */\nassert(ad.fifo_tokens[0]==1&&ad.fifo_tokens[1]==2&&ad.fifo_tokens[2]==1);\nassert(rtmp_tx_swq_exit(&ad,3)==FALSE);assert(!freed[0]&&!freed[2]);\nad.MacTab.tr_entry[2].none=1;assert(rtmp_tx_swq_exit(&ad,2)==TRUE);assert(!freed[2]);\nreturn 0;}\n'
a.output.write_text(PREFIX+body+SUFFIX,encoding='utf-8')
print('Extracted per-WCID cleanup; no concurrent/DMA/RX proof')
