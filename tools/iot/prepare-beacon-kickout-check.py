#!/usr/bin/env python3
"""Guard the final beacon ring kickout; isolated pinned-source candidate."""
import argparse
import hashlib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('fixture', type=Path)
a = p.parse_args()
if len({x.resolve() for x in (a.input, a.candidate, a.fixture)}) != 3 or a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Distinct input and new outputs required')
data = a.input.read_bytes()
if hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() != '82db49fa1822a51268d76f23bce94d886f4d50d6':
    raise SystemExit('Unreviewed beacon kickout source')
source = data.decode()
signature = 'VOID RT28xx_UpdateBeaconToAsic('
if source.count(signature) != 2:
    raise SystemExit('Changed beacon kickout signature')
start = source.index(signature)
end = source.index('\n}', start) + 2
if source.find(signature, start + len(signature)) < end or source[end:].splitlines()[1].strip() != '#endif /* MT_MAC */':
    raise SystemExit('Changed MT_MAC kickout boundary')
function = source[start:end]
lookup = '\t\tbcn_buf = &pAd->ApCfg.MBSSID[apidx].bcn_buf;'
if function.count(lookup) != 1:
    raise SystemExit('Changed BSS lookup')
function = function.replace(lookup, '''\t\tif (apidx < 0 ||
\t\t    (unsigned int)apidx >= sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]) ||
\t\t    apidx >= pAd->ApCfg.BssidNum)
\t\t\treturn;
''' + lookup, 1)
entry = '\tPNDIS_PACKET *pkt = NULL;'
if function.count(entry) != 1:
    raise SystemExit('Changed kickout entry')
function = function.replace(entry, entry + '''
\tif (!pAd) return;''', 1)
kick = '''\t\tRTMP_SEM_LOCK(&pAd->BcnRingLock);
\t\tHAL_KickOutMgmtTx(pAd, Q_IDX_BCN, pkt, buf, len);'''
if function.count(kick) != 1:
    raise SystemExit('Changed kickout lock')
function = function.replace(kick, '''\t\tRTMP_SEM_LOCK(&pAd->BcnRingLock);
\t\t/* Beacon kickout bypasses the ordinary software dequeue gate. */
\t\tif (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET)) {
\t\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);
\t\t\treturn;
\t\t}
#ifdef CONFIG_AP_SUPPORT
\t\t/* Close may have started after the frame was prepared. */
\t\tif (!BeaconTransmitRequired(pAd, apidx, &pAd->ApCfg.MBSSID[apidx])) {
\t\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);
\t\t\treturn;
\t\t}
#endif
\t\tHAL_KickOutMgmtTx(pAd, Q_IDX_BCN, pkt, buf, len);''', 1)
prefix = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef void VOID;
#define IN
typedef int INT;
typedef unsigned int ULONG;
typedef unsigned char UCHAR;
typedef struct packet {UCHAR data[16];INT len;} PNDIS_PACKET;
typedef struct {PNDIS_PACKET *BeaconPkt;INT bcn_state,bBcnSntReq;} BCN_BUF_STRUC;
typedef struct {BCN_BUF_STRUC bcn_buf;INT running;} BSS_STRUCT;
typedef struct {struct {INT tx_hw_hdr_len;} chipCap;
 struct {INT BssidNum;BSS_STRUCT MBSSID[3];} ApCfg;INT BcnRingLock;unsigned int flags;} RTMP_ADAPTER;
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 0x00800000U
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define CONFIG_AP_SUPPORT 1
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if(1)
#define DBGPRINT(level,args) ((void)0)
#define GET_OS_PKT_DATAPTR(pkt) ((pkt)->data)
#define SET_OS_PKT_LEN(pkt,value) ((pkt)->len=(value))
#define RT_DEBUG_ERROR 1
#define Q_IDX_BCN 2
#define BCN_TX_WRITE_TO_DMA 4
static INT mode,held,locks,unlocks,kicks;
static RTMP_ADAPTER *current_ad;
static void take(INT *l){assert(!*l);*l=1;held=1;locks++;
 if(mode==4)current_ad->ApCfg.MBSSID[2].running=0; }
static void drop(INT *l){assert(*l&&held);*l=0;held=0;unlocks++;}
#define RTMP_SEM_LOCK(lock) take(lock)
#define RTMP_SEM_UNLOCK(lock) drop(lock)
static INT BeaconTransmitRequired(RTMP_ADAPTER *ad,INT idx,BSS_STRUCT *bss){
 assert(held&&idx>=0&&idx<ad->ApCfg.BssidNum);
 return bss->bcn_buf.bBcnSntReq&&bss->running;
}
static void HAL_KickOutMgmtTx(RTMP_ADAPTER *ad,INT queue,PNDIS_PACKET *pkt,UCHAR *buf,INT len){
 (void)ad;(void)pkt;(void)buf;(void)len;assert(held&&queue==Q_IDX_BCN);kicks++;
}
'''
tail = r'''
int main(void){
 RTMP_ADAPTER ad;PNDIS_PACKET pkt;
 for(mode=0;mode<7;mode++){
  memset(&ad,0,sizeof(ad));memset(&pkt,0,sizeof(pkt));
  ad.ApCfg.BssidNum=3;ad.chipCap.tx_hw_hdr_len=4;
  ad.ApCfg.MBSSID[2].bcn_buf.BeaconPkt=&pkt;
  ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  ad.ApCfg.MBSSID[2].running=1;
  current_ad=&ad;
  locks=unlocks=kicks=held=0;
  if(mode==3)ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;
  if(mode==5)ad.ApCfg.MBSSID[2].bcn_buf.BeaconPkt=NULL;
  if(mode==6)ad.flags=fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET;
  RT28xx_UpdateBeaconToAsic(mode==0?NULL:&ad,mode==1?3:2,8,0);
  assert(!held&&locks==unlocks);
  if(mode==2){assert(kicks==1&&ad.ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_WRITE_TO_DMA);}
  else {assert(!kicks&&ad.ApCfg.MBSSID[2].bcn_buf.bcn_state!=BCN_TX_WRITE_TO_DMA);}
  if(mode==3||mode==4||mode==6)assert(locks==1);
  if(mode==0||mode==1||mode==5)assert(!locks);
 }
 puts("PASS actual beacon kickout candidate: invalid/closed/reset-gated BSS refuses, lock balanced, active BSS submits; injected packet/ring, no DMA or RF proof");
 return 0;
}
'''
if a.input.read_bytes() != data:
    raise SystemExit('Input changed')
a.candidate.write_text(source[:start] + function + source[end:], encoding='utf-8')
fixture_function = function.replace('{\n\tBCN_BUF_STRUC *bcn_buf',
                                    '{\n\t(void)UpdatePos; /* Unused by this vendor MT_MAC branch. */\n\tBCN_BUF_STRUC *bcn_buf', 1)
if fixture_function == function:
    raise SystemExit('Changed fixture function body')
a.fixture.write_text(prefix + fixture_function + tail, encoding='utf-8')
