#!/usr/bin/env python3
"""Extract reset writer; test capability stores under injected IRQ lock."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'mgmt/mgmt_entrytb.c').read_text();start='VOID tr_tb_reset_entry('
ends=[x for x in ['VOID tr_tb_set_entry(', 'BOOLEAN tr_tb_set_entry('] if s.count(x)==1]
if len(ends)!=1:p.error('unique reviewed TR setup boundary required')
end=ends[0]
if s.count(start)!=1 or s.count(end)!=1:p.error('TR boundaries changed')
body=s[s.index(start):s.index(end)]
if body.count('WRITE_ONCE(tr_entry->enq_cap, FALSE)')!=1:p.error('writer fence missing')
PREFIX='#include <assert.h>\n#define MAX_LEN_OF_TR_TABLE 3\n#define WMM_QUE_NUM 4\n#define FALSE 0\n#define VOID void\n#define WRITE_ONCE(x,v) do{assert(held);(x)=(v);}while(0)\ntypedef unsigned char UCHAR;typedef int INT;typedef unsigned long ULONG;\nstruct _STA_TR_ENTRY {int none,enq_cap,deq_cap,txq_lock[4],ps_queue_lock,high_pkt_cnt,high_pkt_drop_cnt;};\ntypedef struct {int irq_lock;struct {struct _STA_TR_ENTRY tr_entry[3];} MacTab;} RTMP_ADAPTER;\nstatic int held,cleanup,frees;\n#define IS_ENTRY_NONE(e) ((e)->none)\n#define SET_ENTRY_NONE(e) do{assert(!held);(e)->none=1;}while(0)\n#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)\n#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)\nstatic void rtmp_tx_swq_exit(RTMP_ADAPTER *a,UCHAR id){assert(!held);assert(!a->MacTab.tr_entry[id].enq_cap&&!a->MacTab.tr_entry[id].deq_cap);cleanup++;}\n#define NdisFreeSpinLock(l) do{(void)(l);assert(!held);frees++;}while(0)\n'
SUFFIX='\nint main(void){RTMP_ADAPTER a={0};a.MacTab.tr_entry[1].enq_cap=a.MacTab.tr_entry[1].deq_cap=1;\ntr_tb_reset_entry(&a,1);assert(!held&&cleanup==1&&frees==5&&a.MacTab.tr_entry[1].none);\ntr_tb_reset_entry(&a,1);assert(cleanup==1&&frees==5);\ntr_tb_reset_entry(&a,3);assert(!held&&cleanup==1);return 0;}\n'
a.output.write_text(PREFIX+body+SUFFIX,encoding='utf-8')
print('Extracted reset writer; caller locks and real cleanup not proved')
