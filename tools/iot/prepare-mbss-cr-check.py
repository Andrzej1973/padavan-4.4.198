#!/usr/bin/env python3
"""Bound per-BSS register operations; injected register test, no RF/drain proof."""
import argparse
import hashlib
import re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path)
p.add_argument('candidate',type=Path);p.add_argument('fixture',type=Path)
a=p.parse_args()
if len({x.resolve() for x in (a.input,a.candidate,a.fixture)})!=3 or a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Distinct input and new outputs required')
data=a.input.read_bytes()
if hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()!='92d3b01b7be6dd7bcdfe2bc8fbc74b6838ac3b9f':
    raise SystemExit('Unreviewed MBSS source')
s=data.decode();functions=[]
for signature in ('INT32 mbss_cr_enable(PNET_DEV pDev)','INT mbss_cr_disable(PNET_DEV pDev)'):
    if s.count(signature)!=1:raise SystemExit('Changed CR signature')
    start=s.index(signature);end=s.index('\n}',start)+2;f=s[start:end]
    anchor='\tpAd = RTMP_OS_NETDEV_GET_PRIV(pDev);'
    if f.count(anchor)!=1:raise SystemExit('Changed adapter lookup')
    f=f.replace(anchor,'\tif (!pDev) return -1;\n'+anchor+'\n\tif (!pAd) return -1;',1)
    pattern=r'if \(BssId < 0\)\s*return -1;'
    if len(re.findall(pattern,f))!=1:raise SystemExit('Changed index guard')
    f=re.sub(pattern,'''if (BssId < 0 ||
        (unsigned int)pAd->ApCfg.BssidNum > sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]) ||
        (unsigned int)BssId >= sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]) ||
        BssId >= pAd->ApCfg.BssidNum) {
        return -1;
    }''',f,count=1)
    if signature.startswith('INT32 mbss_cr_enable'):
        anchor='    if (BssId >= 1) {'
        if f.count(anchor)!=1:raise SystemExit('Changed enable register block')
        f=f.replace(anchor,'''    if (BssId >= 1) {
        /* Serialize this secondary BSS register transition with disable
         * and recovery; no polls or allocations are inside this section. */
        RTMP_SEM_LOCK(&pAd->BcnRingLock);
        if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET)) {
            RTMP_SEM_UNLOCK(&pAd->BcnRingLock);
            return -1;
        }''',1)
        anchor='\n    }\n\n\treturn 0;'
        if f.count(anchor)!=1:raise SystemExit('Changed enable block end')
        f=f.replace(anchor,'\n        RTMP_SEM_UNLOCK(&pAd->BcnRingLock);'+anchor,1)
    if signature.startswith('INT mbss_cr_disable'):
        anchor='    for (loop = 1; loop < pAd->ApCfg.BssidNum; loop++) {'
        if f.count(anchor)!=1:raise SystemExit('Changed disable peer scan')
        f=f.replace(anchor,'''    /* Serialize close intent with beacon ring submission and recovery.
     * Keep all register operations short; there are no flush polls here. */
    RTMP_SEM_LOCK(&pAd->BcnRingLock);
    pAd->ApCfg.MBSSID[BssId].bcn_buf.bBcnSntReq = FALSE;
'''+anchor,1)
        anchor='\treturn 0;'
        if f.count(anchor)!=1:raise SystemExit('Changed disable return')
        f=f.replace(anchor,'    RTMP_SEM_UNLOCK(&pAd->BcnRingLock);\n'+anchor,1)
    s=s[:start]+f+s[end:];functions.append(f)
prefix=r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT;
typedef int INT32;
typedef unsigned int UINT32;
typedef unsigned char UCHAR;
typedef int BOOLEAN;
typedef struct adapter {struct {int hif_type;} chipCap;struct {
 unsigned char BssidNum;struct {struct {int bBcnSntReq;} bcn_buf;} MBSSID[3];} ApCfg;
 int BcnRingLock;unsigned int flags;} *PRTMP_ADAPTER;
typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;
#define TRUE 1
#define FALSE 0
#define HIF_MT 1
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 0x00800000U
#define RTMP_TEST_FLAG(ad,flag) (((ad)->flags & (flag)) != 0)
#define LPON_SBTOR1 0x100U
#define ARB_BCNQCR0 0x200U
#define SBSS_TBTT0_TSF0_EN 4U
#define TBTT0_n_INT_EN 1U
#define PRE_TBTT0_n_INT_EN 2U
#define SUB_BSSID0_TIME_OFFSET_n_MASK 0xffff0000U
#define SUB_BSSID0_TIME_OFFSET_n(x) ((unsigned int)(x)<<16)
#define printk(...) ((void)0)
#define RTMP_OS_NETDEV_GET_PRIV(dev) ((dev)->ad)
static int index_value,reads,writes,locks,unlocks;
#define RTMP_SEM_LOCK(lock) do {assert(!*(lock));*(lock)=1;locks++;} while(0)
#define RTMP_SEM_UNLOCK(lock) do {assert(*(lock));*(lock)=0;unlocks++;} while(0)
static unsigned int lpon[2],arb;
static int RT28xx_MBSS_IdxGet(PRTMP_ADAPTER ad,PNET_DEV dev){assert(ad&&dev);return index_value;}
static unsigned int *reg(unsigned int address){
 if(address==ARB_BCNQCR0)return &arb;
 assert(address>=LPON_SBTOR1&&address<=LPON_SBTOR1+4&&!(address&3));
 return &lpon[(address-LPON_SBTOR1)/4];
}
#define RTMP_IO_READ32(ad,address,value) (assert((ad)->BcnRingLock),reads++,*(value)=*reg(address))
#define RTMP_IO_WRITE32(ad,address,value) (assert((ad)->BcnRingLock),writes++,*reg(address)=(value))
'''
tail=r'''
int main(void){
 struct adapter ad;struct device dev;unsigned int initial;int ret;
 for(int enable=0;enable<2;enable++)for(int mode=0;mode<10;mode++){
  memset(&ad,0,sizeof(ad));ad.chipCap.hif_type=mode==7?0:1;
  if(mode==9)ad.flags=fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET;
  ad.ApCfg.BssidNum=mode==3?2:mode==5?4:3;
  for(int i=0;i<3;i++)ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq=1;
  index_value=mode==2?-1:mode==4?3:mode==8?0:2;
  dev.ad=mode==1?NULL:&ad;reads=writes=locks=unlocks=0;
  lpon[0]=0xabc00007;lpon[1]=0xdef00007;initial=arb=0xf00fffff;
  ret=enable?mbss_cr_enable(mode==0?NULL:&dev):mbss_cr_disable(mode==0?NULL:&dev);
  if(mode<=5)assert(ret==-1&&!reads&&!writes&&arb==initial&&!locks&&!unlocks);
  else if(mode==7)assert(!ret&&!reads&&!writes&&arb==initial&&!locks&&!unlocks);
  else if(mode==8){
   assert(!ret&&!reads&&!writes&&arb==initial);
   assert(locks==(!enable)&&unlocks==(!enable)&&!ad.BcnRingLock);
  }
  else if(mode==9&&enable){
   assert(ret==-1&&!reads&&!writes&&arb==initial);
   assert(locks==1&&unlocks==1&&!ad.BcnRingLock);
  }
  else {
   unsigned int bit=1U<<(index_value+15);
   assert(!ret&&reads&&writes&&(arb&~bit)==(initial&~bit));
   assert((arb&bit)==(enable?bit:0));
   if(!enable)assert(lpon[0]==0xabc00007); /* Other BSS timing preserved. */
   assert(locks==1&&unlocks==1&&!ad.BcnRingLock);
   if(!enable){
    for(int i=0;i<3;i++)assert(ad.ApCfg.MBSSID[i].bcn_buf.bBcnSntReq==(i!=index_value));}
  }
 }
 puts("PASS actual MBSS CR candidates: invalid/inactive/count-overflow and dequeue-disabled state reject before register IO; selected queue bit preserved peers; registers injected, no RF/drain proof");
 return 0;
}
'''
if a.input.read_bytes()!=data:raise SystemExit('Input changed')
a.candidate.write_text(s,encoding='utf-8')
a.fixture.write_text(prefix+'\n'.join(functions)+tail,encoding='utf-8')
