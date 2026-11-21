#!/usr/bin/env python3
"""Stage early MBSS close bounds checks; no hardware drain/RF proof."""
import argparse
import hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path)
p.add_argument('candidate',type=Path);p.add_argument('fixture',type=Path)
a=p.parse_args()
if len({x.resolve() for x in (a.input,a.candidate,a.fixture)})!=3 or a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Input/output paths must be distinct and outputs new')
data=a.input.read_bytes();s=data.decode('utf-8')
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f':
    raise SystemExit('Unreviewed MBSS source')
anchor='INT MBSS_Close(PNET_DEV pDev)'
if s.count(anchor)!=1:raise SystemExit('Changed close signature')
start=s.index(anchor);end=s.index('\n}',start)+2;f=s[start:end]
old='''\tu4MaxMBSSIDSize = sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]);
\tif(BssId >= u4MaxMBSSIDSize)
\t{
\t\tDBGPRINT(RT_DEBUG_ERROR, ("%s(): Over buffer size!\\n", __FUNCTION__));
\t    return -1;
\t}'''
if f.count(old)!=1:raise SystemExit('Changed late bounds block')
f=f.replace(old,'',1)
old='\tpAd = RTMP_OS_NETDEV_GET_PRIV(pDev);'
if f.count(old)!=1:raise SystemExit('Changed adapter lookup')
f=f.replace(old,'\tif (!pDev)\n\t\treturn -1;\n'+old+'\n\tif (!pAd)\n\t\treturn -1;',1)
old='''    if (BssId < 0)
        return -1;'''
if f.count(old)!=1:raise SystemExit('Changed negative index guard')
f=f.replace(old,'''    u4MaxMBSSIDSize = sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]);
    if (BssId < 0 || (UINT32)BssId >= u4MaxMBSSIDSize ||
        BssId >= pAd->ApCfg.BssidNum) {
        return -1;
    }''',1)
prefix=r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT;
typedef unsigned int UINT32;
struct device;
typedef struct adapter {struct {int BssidNum;struct {struct {int bBcnSntReq;} bcn_buf;} MBSSID[3];} ApCfg;} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;
#define FALSE 0
#define REASON_DISASSOC_INACTIVE 4
static int index_value,stops,kicks,makes,updates;
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
static int RT28xx_MBSS_IdxGet(PRTMP_ADAPTER ad,PNET_DEV dev){assert(ad&&dev);return index_value;}
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) ((void)(dev),stops++)
static void MbssKickOutStas(PRTMP_ADAPTER ad,int index,int reason){
 assert(ad&&index>=0&&index<ad->ApCfg.BssidNum&&index<3&&reason==4);kicks++;
}
#define APMakeAllBssBeacon(ad) ((void)(ad),makes++)
#define APUpdateAllBeaconFrame(ad) ((void)(ad),updates++)
'''
tail=r'''
int main(void){
 struct adapter ad;struct device dev;dev.ad=&ad;
 for(int mode=0;mode<7;mode++){
  memset(&ad,0,sizeof(ad));ad.ApCfg.BssidNum=mode==3?2:3;
  for(int i=0;i<3;i++)ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq=1;
  stops=kicks=makes=updates=0;index_value=mode==2?-1:mode==4?3:mode==6?1:2;
  dev.ad=mode==1?NULL:&ad;
  int ret=MBSS_Close(mode==0?NULL:&dev);
  if(mode<=4){
   assert(ret==-1&&!stops&&!kicks&&!makes&&!updates);
   for(int i=0;i<3;i++)assert(ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq);
  }else{
   assert(!ret&&stops==1&&kicks==1&&makes==1&&updates==1);
   for(int i=0;i<3;i++)assert(ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq==(i!=index_value));
  }
 }
 puts("PASS actual MBSS_Close candidate: null/negative/inactive/out-of-array reject before effects; selected beacon intent only; no RF/drain proof");
 return 0;
}
'''
if a.input.read_bytes()!=data:raise SystemExit('Input changed')
a.candidate.write_text(s[:start]+f+s[end:],encoding='utf-8')
a.fixture.write_text(prefix+f+tail,encoding='utf-8')
