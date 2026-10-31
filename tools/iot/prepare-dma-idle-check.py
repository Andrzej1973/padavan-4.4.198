#!/usr/bin/env python3
"""Prepare a separate checked DMA-poll candidate, not a radio-off installer."""
import argparse
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('fixture', type=Path)
a = p.parse_args()
if len({x.resolve() for x in (a.input, a.candidate, a.fixture)}) != 3:
    raise SystemExit('Input and outputs must be distinct')
if a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Refusing to overwrite outputs')
source = a.input.read_text(encoding='utf-8')
anchor = 'VOID MTPciPollTxRxEmpty(RTMP_ADAPTER *pAd)'
checked_anchor = 'BOOLEAN wr_iot_mt_poll_txrx_empty(RTMP_ADAPTER *pAd)'
if source.count(anchor) != 1 or source.count(checked_anchor) > 1:
    raise SystemExit('DMA poll source changed')
already_checked = checked_anchor in source
start = source.index(anchor)
end = source.index('\n}', start) + 2
original = source[start:end]
checked = original.replace(anchor, 'BOOLEAN wr_iot_mt_poll_txrx_empty(RTMP_ADAPTER *pAd)', 1)
entry = '\tRtmpOsMsDelay(100);'
if checked.count(entry) != 1:
    raise SystemExit('DMA poll entry changed')
checked = checked.replace(entry, '''    /* Caller serializes radio writers. Do not consume another poll's flag. */
    if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE)) {
        return FALSE;
    }
''' + entry, 1)
early = '\t\tif (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST))\n\t\t\treturn;'
if checked.count(early) != 2:
    raise SystemExit('DMA poll disappearance branches changed')
checked = checked.replace(early, '''        if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST)) {
            RTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);
            return FALSE;
        }''')
idle = '\t\t\tRtmpusecDelay(50);\n\t\t}'
if checked.count(idle) != 2:
    raise SystemExit('DMA idle window changed')
checked = checked.replace(idle, idle + ' else {\n            IdleTimes = 0;\n        }')
timeout = '\tif (Loop >= PollLoopTimesThreshold)\n\t{'
if checked.count(timeout) != 2:
    raise SystemExit('DMA timeout branches changed')
timeout_end = '__FUNCTION__, Value));\n\t}'
if checked.count(timeout_end) != 2:
    raise SystemExit('DMA timeout diagnostics changed')
checked = checked.replace(timeout_end, '__FUNCTION__, Value));\n        RTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);\n        return FALSE;\n\t}')
finish = '\tRTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);\n}'
if checked.count(finish) != 1:
    raise SystemExit('DMA completion changed')
old_checked = checked.replace(finish, '\tRTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);\n    return TRUE;\n}')
checked = checked.replace(finish, '''    /* A disappearance on the final RX read is not an idle receipt. */
    if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST)) {
        RTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);
        return FALSE;
    }
\tRTMP_CLEAR_FLAG(pAd, fRTMP_ADAPTER_POLL_IDLE);
    return TRUE;
}''')
if already_checked:
    existing_start = source.index(checked_anchor)
    existing_end = source.index('\n}', existing_start) + 2
    existing = source[existing_start:existing_end]
    if existing not in (old_checked, checked):
        raise SystemExit('Existing checked DMA poll differs from generated helper')
prefix = r'''#include <assert.h>
#include <stdio.h>
typedef unsigned int UINT32;
typedef int BOOLEAN;
typedef struct {unsigned int flags;} RTMP_ADAPTER;
#define TRUE 1
#define FALSE 0
#define fRTMP_ADAPTER_POLL_IDLE 1u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 2u
#define MT_WPDMA_GLO_CFG 1
#define TX_DMA_BUSY 1u
#define RX_DMA_BUSY 2u
#define RT_DEBUG_OFF 0
#define DBGPRINT(level,args) ((void)0)
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define RTMP_SET_FLAG(ad,flag) ((ad)->flags|=(flag))
#define RTMP_CLEAR_FLAG(ad,flag) ((ad)->flags&=~(flag))
static int mode,reads,delays;
static UINT32 read_dma(RTMP_ADAPTER *ad){
 reads++;
 if(mode==1)return TX_DMA_BUSY|RX_DMA_BUSY;
 if(mode==2)return reads%2?0:TX_DMA_BUSY|RX_DMA_BUSY;
 if(mode==3&&reads==10)ad->flags|=fRTMP_ADAPTER_NIC_NOT_EXIST;
 if(mode==4&&reads>5001)return RX_DMA_BUSY;
 if(mode==5&&reads==5011)ad->flags|=fRTMP_ADAPTER_NIC_NOT_EXIST;
 if(mode==6&&reads==10002)ad->flags|=fRTMP_ADAPTER_NIC_NOT_EXIST;
 return 0;
}
#define RTMP_IO_READ32(ad,reg,value) ((void)(reg),*(value)=read_dma(ad))
static void RtmpOsMsDelay(int n){assert(n==100);delays++;}
static void RtmpusecDelay(int n){assert(n==50);}
'''
tail = r'''
int main(void){
 RTMP_ADAPTER ad={0};
 assert(wr_iot_mt_poll_txrx_empty(&ad)&&!ad.flags&&reads==10002&&delays==1);
 for(mode=1;mode<=6;mode++){
  ad.flags=0;reads=delays=0;
  assert(!wr_iot_mt_poll_txrx_empty(&ad));
  assert(!(ad.flags&fRTMP_ADAPTER_POLL_IDLE));
  if(mode==1||mode==2)assert(reads==20000);
  if(mode==3)assert(reads==10&&(ad.flags&fRTMP_ADAPTER_NIC_NOT_EXIST));
  if(mode==4)assert(reads==25001);
  if(mode==5)assert(reads==5011&&(ad.flags&fRTMP_ADAPTER_NIC_NOT_EXIST));
  if(mode==6)assert(reads==10002&&(ad.flags&fRTMP_ADAPTER_NIC_NOT_EXIST));
 }
 ad.flags=fRTMP_ADAPTER_POLL_IDLE;reads=delays=0;
 assert(!wr_iot_mt_poll_txrx_empty(&ad)&&ad.flags==fRTMP_ADAPTER_POLL_IDLE&&!reads&&!delays);
 puts("PASS separate checked DMA poll: consecutive idle, TX/RX timeout, intermittent busy, TX/RX disappearance and foreign flag; register reads injected, no RF proof");
 return 0;
}
'''
# Keep the existing shared void function and all its callers untouched.
a.candidate.write_text((source[:existing_start] + checked + source[existing_end:])
                       if already_checked else source[:start] + checked + '\n\n' + source[start:],
                       encoding='utf-8')
a.fixture.write_text(prefix + checked + tail, encoding='utf-8')
print('Prepared checked DMA poll with final-read disappearance guard; original radio-off path unchanged')
