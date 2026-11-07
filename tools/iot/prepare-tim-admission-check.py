#!/usr/bin/env python3
"""Exercise the generated TIM ring admission against an injected close race."""

import argparse
from pathlib import Path


parser = argparse.ArgumentParser()
parser.add_argument('candidate', type=Path)
parser.add_argument('fixture', type=Path)
args = parser.parse_args()
if args.fixture.exists() or args.candidate.resolve() == args.fixture.resolve():
    parser.error('Fixture must be a new path separate from the candidate')

source = args.candidate.read_text(encoding='utf-8')
signature = 'VOID RT28xx_UpdateTimToAsic('
if source.count(signature) != 1:
    parser.error('TIM sender signature changed')
start = source.index(signature)
end = source.index('\n}', start) + 2
function = source[start:end]
for required in ('apidx >= pAd->ApCfg.BssidNum',
                 'RTMP_SEM_LOCK(&pAd->BcnRingLock);',
                 '!pAd->ApCfg.MBSSID[apidx].bcn_buf.bBcnSntReq',
                 'HAL_KickOutMgmtTx(pAd, Q_IDX_BCN, pkt, buf, len)'):
    if function.count(required) != 1:
        parser.error('TIM admission gate changed: ' + required)

fixture = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef void VOID;
#define IN
typedef int INT;
typedef unsigned long ULONG;
typedef unsigned char UCHAR;
typedef struct { UCHAR data[32]; INT len; } packet;
typedef packet *PNDIS_PACKET;
typedef struct { PNDIS_PACKET TimPkt; } TIM_BUF_STRUC;
typedef struct { struct { INT bBcnSntReq; } bcn_buf; TIM_BUF_STRUC tim_buf; } BSS_STRUCT;
typedef struct { struct { INT BssidNum; BSS_STRUCT MBSSID[3]; } ApCfg;
                 struct { INT tx_hw_hdr_len; } chipCap; INT BcnRingLock; } RTMP_ADAPTER;
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if (1)
#define DBGPRINT(level,args) ((void)0)
#define RT_DEBUG_ERROR 1
#define GET_OS_PKT_DATAPTR(pkt) ((pkt)->data)
#define SET_OS_PKT_LEN(pkt,value) ((pkt)->len=(value))
#define Q_IDX_BCN 2
static INT mode, held, locks, unlocks, kicks;
static RTMP_ADAPTER *current;
static void take(INT *lock) {
 assert(!*lock && !held); *lock=1; held=1; locks++;
 if(mode==4)current->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;
}
static void drop(INT *lock) { assert(*lock && held); *lock=0; held=0; unlocks++; }
#define RTMP_SEM_LOCK(lock) take(lock)
#define RTMP_SEM_UNLOCK(lock) drop(lock)
static void HAL_KickOutMgmtTx(RTMP_ADAPTER *ad, INT queue, PNDIS_PACKET pkt,
                              UCHAR *buf, INT len) {
 (void)ad;(void)pkt;(void)buf;(void)len;
 assert(held && queue==Q_IDX_BCN); kicks++;
}
''' + function + r'''
int main(void) {
 RTMP_ADAPTER ad; packet pkt;
 for(mode=0;mode<8;mode++) {
  memset(&ad,0,sizeof(ad)); memset(&pkt,0,sizeof(pkt));
  ad.ApCfg.BssidNum=3; ad.chipCap.tx_hw_hdr_len=4;
  ad.ApCfg.MBSSID[2].tim_buf.TimPkt=&pkt;
  ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  ad.ApCfg.MBSSID[0].tim_buf.TimPkt=&pkt;
  current=&ad; held=locks=unlocks=kicks=0;
  if(mode==3)ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;
  if(mode==7)ad.ApCfg.MBSSID[2].tim_buf.TimPkt=NULL;
  RT28xx_UpdateTimToAsic(mode==0?NULL:&ad,
                         mode==1?-1:mode==2?3:mode==6?0:2,8);
  assert(!held && locks==unlocks);
  if(mode==5 || mode==6)assert(kicks==1 && locks==1);
  else assert(kicks==0);
  if(mode==3 || mode==4)assert(locks==1);
  if(mode==0 || mode==1 || mode==2 || mode==7)assert(locks==0);
 }
 puts("PASS generated TIM admission: bounds, close-before/at-lock, peers");
 return 0;
}
'''
args.fixture.parent.mkdir(parents=True, exist_ok=True)
args.fixture.write_text(fixture, encoding='utf-8')
