#!/usr/bin/env python3
"""Prepare a pinned, isolated MBSS_Open state candidate and host fixture."""
import argparse
import hashlib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('input', type=Path)
p.add_argument('candidate', type=Path)
p.add_argument('fixture', type=Path)
a = p.parse_args()
if len({x.resolve() for x in (a.input, a.candidate, a.fixture)}) != 3 or a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Distinct input and new output paths required')
data = a.input.read_bytes()
blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
if blob != '92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f':
    raise SystemExit('Unreviewed MBSS source')
source = data.decode('utf-8')
signature = 'INT32 MBSS_Open(PNET_DEV pDev)'
if source.count(signature) != 1:
    raise SystemExit('Changed MBSS_Open signature')
start = source.index(signature)
end = source.index('\n}', start) + 2
f = source[start:end]
old = '''\tu4MaxMBSSIDSize = sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]);
\tpAd = RTMP_OS_NETDEV_GET_PRIV(pDev);
\tBssId = RT28xx_MBSS_IdxGet(pAd, pDev);
\tif (BssId < 0)
\t\treturn -1;

\tif(BssId >= u4MaxMBSSIDSize)
\t{
\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): Over buffer size!\\n", __FUNCTION__));
\t\treturn -1;
\t}'''
new = '''\tif (!pDev)
\t\treturn -1;
\tpAd = RTMP_OS_NETDEV_GET_PRIV(pDev);
\tif (!pAd)
\t\treturn -1;
\tu4MaxMBSSIDSize = sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]);
\t/* IdxGet iterates BssidNum, so bound the count before calling it. */
\tif (pAd->ApCfg.BssidNum > u4MaxMBSSIDSize)
\t\treturn -1;
\tBssId = RT28xx_MBSS_IdxGet(pAd, pDev);
\t/* This wrapper opens secondary interfaces only; protect the main BSS. */
\tif (BssId <= 0 || (UINT32)BssId >= u4MaxMBSSIDSize ||
\t    (UINT32)BssId >= pAd->ApCfg.BssidNum)
\t\treturn -1;'''
if f.count(old) != 1:
    raise SystemExit('Changed MBSS_Open validation')
f = f.replace(old, new, 1)
flag_start = '#ifdef AIRPLAY_SUPPORT\n'
flag_end = '#endif /* AIRPLAY_SUPPORT */'
if f.count(flag_start) != 1 or f.count(flag_end) != 1:
    raise SystemExit('Changed beacon-intent block')
f = f.replace(flag_start, '''/* Coordinate beacon intent with close, final kickout and recovery. */
\tRTMP_SEM_LOCK(&pAd->BcnRingLock);
\tif (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET)) {
\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);
\t\treturn -1;
\t}
'''+flag_start, 1)
f = f.replace(flag_end, flag_end+'\n\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);', 1)
candidate = source[:start] + f + source[end:]
prefix = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT;
typedef int INT32;
typedef unsigned int UINT32;
typedef struct adapter {struct {UINT32 BssidNum;int BandSteering;
 struct {struct {int bBcnSntReq;} bcn_buf;struct {int marker;} wdev;} MBSSID[3];
 } ApCfg;int BcnRingLock;int airplay;unsigned int flags;} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;
typedef int *PBND_STRG_CLI_TABLE;
#define TRUE 1
#define FALSE 0
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
#define AIRPLAY_ON(ad) ((ad)->airplay)
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 0x00800000U
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define RTMP_SEM_LOCK(lock) do {assert(!*(lock));*(lock)=1;locks++;} while(0)
#define RTMP_SEM_UNLOCK(lock) do {assert(*(lock));*(lock)=0;unlocks++;} while(0)
static int index_value,idx_calls,locks,unlocks,band_calls,band_flag;
static INT32 RT28xx_MBSS_IdxGet(PRTMP_ADAPTER ad,PNET_DEV dev){
 assert(ad&&dev&&ad->ApCfg.BssidNum<=3);idx_calls++;return index_value;
}
#ifdef BAND_STEERING
static int band_table;
static PBND_STRG_CLI_TABLE Get_BndStrgTable(PRTMP_ADAPTER ad,INT index){
 assert(ad&&index>0&&index<3);return &band_table;
}
static void BndStrg_SetInfFlags(PRTMP_ADAPTER ad,void *wdev,PBND_STRG_CLI_TABLE table,int flag){
 assert(ad&&wdev&&table==&band_table&&!ad->BcnRingLock);band_calls++;band_flag=flag;
}
#endif
'''
tail = r'''
int main(void){
 struct adapter ad;struct device dev;
 (void)band_flag;
 for(int mode=0;mode<9;mode++){
  memset(&ad,0,sizeof(ad));ad.ApCfg.BssidNum=mode==2?4:mode==5?1:3;
  ad.ApCfg.BandSteering=1;ad.airplay=mode!=7;
  if(mode==8)ad.flags=fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET;
  for(int i=0;i<3;i++)ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq=0;
  dev.ad=mode==1?NULL:&ad;
  index_value=mode==3?-1:mode==4?0:mode==6?3:2;
  idx_calls=locks=unlocks=band_calls=band_flag=0;
  int ret=MBSS_Open(mode==0?NULL:&dev);
  if(mode<=6){
   assert(ret==-1&&!locks&&!unlocks&&!band_calls);
   assert(idx_calls==((mode==3||mode==4||mode==5||mode==6)?1:0));
   for(int i=0;i<3;i++)assert(!ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq);
  }else if(mode==8){
   assert(ret==-1&&idx_calls==1&&locks==1&&unlocks==1&&!ad.BcnRingLock&&!band_calls);
   for(int i=0;i<3;i++)assert(!ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq);
  }else{
   assert(!ret&&idx_calls==1&&locks==1&&unlocks==1&&!ad.BcnRingLock);
#ifdef AIRPLAY_SUPPORT
   assert(!ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq);
#else
   assert(ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq);
#endif
#ifdef BAND_STEERING
   assert(band_calls==1&&band_flag==1);
#else
   assert(!band_calls);
#endif
   assert(!ad.ApCfg.MBSSID[0].bcn_buf.bBcnSntReq);
  }
 }
 puts("PASS pinned MBSS_Open candidate: bounds before lookup, main BSS protected, reset gate refuses before intent, lock balanced");
 return 0;
}
'''
if a.input.read_bytes() != data:
    raise SystemExit('Input changed')
a.candidate.write_text(candidate, encoding='utf-8')
a.fixture.write_text(prefix+f+tail, encoding='utf-8')
