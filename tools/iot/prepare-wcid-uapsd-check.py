#!/usr/bin/env python3
"""Extract UAPSD insertion into injected host lock/admission tests."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'common/uapsd.c').read_text();start='VOID UAPSD_PacketEnqueue(';end='VOID UAPSD_SP_PacketCheck('
if s.count(start)!=1 or s.count(end)!=1:p.error('UAPSD function boundaries changed')
body=s[s.index(start):s.index(end)];body=body[:body.rindex('#ifdef RTMP_MAC_PCI')]
if body.count('READ_ONCE(pAd->MacTab.tr_entry[pEntry->wcid].enq_cap)')!=1:p.error('admission fence missing')
PREFIX='#include <assert.h>\n#include <stddef.h>\n#define IN\n#define FALSE 0\n#define MAX_LEN_OF_TR_TABLE 3\n#define MAX_PACKETS_IN_UAPSD_QUEUE 4\n#define NDIS_STATUS_FAILURE -1\n#define RT_DEBUG_TRACE 0\n#define DBGPRINT(level,args) do{(void)(level);}while(0)\n#define READ_ONCE(x) (x)\ntypedef void VOID;typedef unsigned int UINT32;typedef unsigned long ULONG;typedef int BOOLEAN;\ntypedef struct {unsigned int Number;} QUEUE_HEADER;\ntypedef struct {unsigned int wcid;QUEUE_HEADER UAPSDQueue[4];} MAC_TABLE_ENTRY;\ntypedef struct {int UAPSDEOSPLock;struct {struct {int enq_cap;} tr_entry[3];} MacTab;} RTMP_ADAPTER;\ntypedef void *PNDIS_PACKET;\nstatic int lock,drops,heads,tails,race_full;\n#define UAPSD_SEM_LOCK(l,f) do{(void)(l);(f)=0;assert(!lock);lock=1;if(race_full)pQueUapsd->Number=4;}while(0)\n#define UAPSD_SEM_UNLOCK(l,f) do{(void)(l);(void)(f);assert(lock);lock=0;}while(0)\n#define RELEASE_NDIS_PACKET(a,p,status) do{(void)(a);(void)(p);(void)(status);drops++;}while(0)\n#define PACKET_TO_QUEUE_ENTRY(p) (p)\n#define InsertHeadQueue(q,p) do{(void)(p);assert(lock);(q)->Number++;heads++;}while(0);\n#define InsertTailQueue(q,p) do{(void)(p);assert(lock);(q)->Number++;tails++;}while(0)\n'
SUFFIX='\nint main(void){RTMP_ADAPTER a={0};MAC_TABLE_ENTRY e={0};int packet;\ne.wcid=1;UAPSD_PacketEnqueue(&a,&e,&packet,0,0);assert(drops==1&&!heads&&!tails&&!lock);\na.MacTab.tr_entry[1].enq_cap=1;UAPSD_PacketEnqueue(&a,&e,&packet,0,0);assert(tails==1&&!lock);\nUAPSD_PacketEnqueue(&a,&e,&packet,1,1);assert(heads==1&&!lock);\nrace_full=1;UAPSD_PacketEnqueue(&a,&e,&packet,2,0);assert(drops==2&&tails==1&&!lock);\nrace_full=0;e.wcid=99;UAPSD_PacketEnqueue(&a,&e,&packet,3,0);assert(drops==3&&!lock);\nUAPSD_PacketEnqueue(&a,NULL,&packet,0,0);assert(drops==4&&!lock);return 0;}\n'
a.output.write_text(PREFIX+body+SUFFIX,encoding='utf-8')
print('Extracted UAPSD insertion; real IRQ/lock-order/retirement not proved')
