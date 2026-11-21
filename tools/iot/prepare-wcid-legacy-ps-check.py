#!/usr/bin/env python3
"""Extract legacy PS enqueue into injected host admission/capacity tests."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'common/ps.c').read_text();start='NDIS_STATUS RtmpInsertPsQueue(';end='VOID RtmpCleanupPsQueue('
if s.count(start)!=1 or s.count(end)!=1:p.error('PS boundaries changed')
body=s[s.index(start):s.index(end)]
if body.count('if (!tr_entry->enq_cap || tr_entry->ps_queue.Number >= MAX_PACKETS_IN_PS_QUEUE)')!=1:p.error('locked PS fence missing')
PREFIX='#include <assert.h>\n#include <stddef.h>\n#define IN\n#define UAPSD_SUPPORT 1\n#define MAX_PACKETS_IN_PS_QUEUE 4\n#define QID_AC_BE 0\n#define NDIS_STATUS_FAILURE -1\n#define NDIS_STATUS_SUCCESS 0\n#define RT_DEBUG_TRACE 0\n#define DBGPRINT(level,args) do{(void)(level);}while(0)\ntypedef int NDIS_STATUS;typedef unsigned int UINT32;typedef unsigned char UCHAR;typedef unsigned long ULONG;\ntypedef struct {int Number;} QUEUE_HEADER;\ntypedef struct {int enq_cap;QUEUE_HEADER ps_queue;} STA_TR_ENTRY;\ntypedef struct {int irq_lock;struct {STA_TR_ENTRY tr_entry[2];} MacTab;} RTMP_ADAPTER;\ntypedef struct {unsigned int wcid;} MAC_TABLE_ENTRY;\ntypedef void *PNDIS_PACKET;\nstatic int lock,freed,inserts,race_full;\n#define UAPSD_MR_IS_UAPSD_AC(entry,id) ((void)(entry),(void)(id),0)\n#define UAPSD_PacketEnqueue(a,e,p,id,h) do{(void)(a);(void)(e);(void)(p);(void)(id);(void)(h);assert(0);}while(0)\n#define FALSE 0\n#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!lock);lock=1;if(race_full)tr_entry->ps_queue.Number=4;}while(0)\n#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(lock);lock=0;}while(0)\n#define RELEASE_NDIS_PACKET(a,p,s) do{(void)(a);(void)(p);(void)(s);freed++;}while(0)\n#define PACKET_TO_QUEUE_ENTRY(p) (p)\n#define InsertTailQueue(q,p) do{(void)(p);assert(lock);(q)->Number++;inserts++;}while(0)\n'
SUFFIX='int main(void){RTMP_ADAPTER a={0};MAC_TABLE_ENTRY e={1};int packet;\nassert(RtmpInsertPsQueue(&a,&packet,&e,0)==-1);assert(freed==1&&!inserts&&!lock);\na.MacTab.tr_entry[1].enq_cap=1;assert(RtmpInsertPsQueue(&a,&packet,&e,0)==0);assert(inserts==1&&!lock);\na.MacTab.tr_entry[1].ps_queue.Number=0;race_full=1;assert(RtmpInsertPsQueue(&a,&packet,&e,0)==-1);assert(inserts==1&&freed==2&&!lock);\nreturn 0;}\n'
a.output.write_text(PREFIX+body+SUFFIX,encoding='utf-8')
print('Extracted legacy PS admission; UAPSD branch not exercised')
