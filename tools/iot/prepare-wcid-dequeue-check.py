#!/usr/bin/env python3
"""Extract actual candidate dequeue selector into bounded host scheduling tests."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():p.error('new output required')
s=(a.candidate/'common/cmm_data.c').read_text();marker='INT rtmp_deq_req(RTMP_ADAPTER *pAd, INT cnt, struct dequeue_info *info)'
if s.count(marker)!=1:p.error('selector boundary changed')
start=s.index(marker);end='INT rtmp_deq_report('
if s.count(end)!=1:p.error('report boundary changed')
body=s[start:s.index(end,start)]
if body.count('wr_iot_wcid_fifo_retire(')!=1:p.error('retirement selector binding missing')
PREFIX='#include "wcid-fifo-retirement.h"\n#include <assert.h>\n#include <string.h>\n#define WMM_QUE_NUM 4\n#define MAX_LEN_OF_TR_TABLE 3\n#define TX_SWQ_FIFO_LEN 4\n#define TRUE 1\n#define FALSE 0\n#define NDIS_STATUS_FAILURE -1\n#define NDIS_STATUS_SUCCESS 0\n#define ENTRY_CAT_MCAST 7\n#define PWR_SAVE 1\n#define APPS_RETRIEVE_IDLE 0\n#define APPS_RETRIEVE_DONE 1\n#define DBGPRINT(level,args) do{}while(0)\n#define INC_RING_INDEX(i,n) do{(i)=((i)+1)%(n);}while(0)\n#define TR_TOKEN_COUNT_INC(e,q) do{(void)(e);(void)(q);}while(0)\ntypedef int INT;typedef unsigned char UCHAR;typedef signed char CHAR;\nstruct tx_swq_fifo {UCHAR swq[4];unsigned int enqIdx,deqIdx;};\ntypedef struct {int deq_cap,EntryType,PsMode,ps_state;struct {unsigned int Number;} tx_queue[4];} STA_TR_ENTRY;\ntypedef struct {struct {STA_TR_ENTRY tr_entry[3];int fAnyStationInPsm;} MacTab;struct tx_swq_fifo tx_swq[4];} RTMP_ADAPTER;\nstruct dequeue_info {int inited;UCHAR start_q,end_q;CHAR cur_q;UCHAR target_wcid,target_que,cur_wcid,q_max_cnt[4];int pkt_cnt,status,status_2,full_qid[4];};\nstatic void rtmp_psDeq_req(RTMP_ADAPTER *a){(void)a;}\n'
SUFFIX='\nstatic struct dequeue_info global(void){struct dequeue_info i={0};i.target_wcid=MAX_LEN_OF_TR_TABLE;i.target_que=0;return i;}\nint main(void){RTMP_ADAPTER a={0};struct dequeue_info i;\na.MacTab.tr_entry[2].deq_cap=1;a.tx_swq[0].swq[0]=1;a.tx_swq[0].swq[1]=1;a.tx_swq[0].swq[2]=2;a.tx_swq[0].enqIdx=3;\ni=global();assert(rtmp_deq_req(&a,4,&i));assert(i.status==0&&i.cur_wcid==2&&a.tx_swq[0].deqIdx==2);assert(a.tx_swq[0].swq[2]==2&&!a.tx_swq[0].swq[0]&&!a.tx_swq[0].swq[1]);\ni=global();i.target_wcid=1;rtmp_deq_req(&a,4,&i);assert(i.status==-1);\nmemset(a.tx_swq,0,sizeof(a.tx_swq));i=global();rtmp_deq_req(&a,4,&i);assert(i.status==-1);\na.tx_swq[0].swq[0]=1;a.tx_swq[0].swq[1]=2;a.tx_swq[0].swq[2]=1;a.tx_swq[0].swq[3]=2;i=global();rtmp_deq_req(&a,4,&i);assert(i.status==0&&i.cur_wcid==2&&a.tx_swq[0].deqIdx==1);assert(a.tx_swq[0].swq[1]==2&&a.tx_swq[0].swq[3]==2);\na.tx_swq[0].swq[1]=99;i=global();rtmp_deq_req(&a,4,&i);assert(i.status==-1);\nreturn 0;}\n'
a.output.write_text(PREFIX+body+SUFFIX,encoding='utf-8')
print('Extracted actual dequeue selector; lock/kernel/DMA primitives not proved')
