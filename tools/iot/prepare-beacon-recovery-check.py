#!/usr/bin/env python3
"""Fail closed on beacon recovery flush timeout; no concurrency/RF proof."""
import argparse
import hashlib
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('input',type=Path)
p.add_argument('candidate',type=Path);p.add_argument('fixture',type=Path)
a=p.parse_args()
if len({x.resolve() for x in (a.input,a.candidate,a.fixture)})!=3 or a.candidate.exists() or a.fixture.exists():
    raise SystemExit('Distinct input and new outputs required')
d=a.input.read_bytes()
if hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()!='a8c0c0ec59c7e51c88296111934597064cf36c4a':
    raise SystemExit('Unreviewed beacon source')
s=d.decode();sig='VOID APCheckBcnQHandler(RTMP_ADAPTER *pAd, INT apidx, BOOLEAN *is_pretbtt_int)'
if s.count(sig)!=1:raise SystemExit('Changed recovery signature')
start=s.index(sig);end=s.index('\n}',start)+2;f=s[start:end]
anchor='\tif (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_HALT_IN_PROGRESS))'
if f.count(anchor)!=1:raise SystemExit('Changed halt guard')
f=f.replace(anchor,'''    if (!is_pretbtt_int) return;
    *is_pretbtt_int = FALSE;
    if (!pAd || apidx < 0 ||
        (unsigned int)apidx >= sizeof(pAd->ApCfg.MBSSID)/sizeof(pAd->ApCfg.MBSSID[0]) ||
        apidx >= pAd->ApCfg.BssidNum) return;
'''+anchor.replace('fRTMP_ADAPTER_HALT_IN_PROGRESS',
                   'fRTMP_ADAPTER_HALT_IN_PROGRESS | fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET'),1)
for message in ('bcn_flush too long!, j = %x','flush all stuck bcn too long!! j = %x'):
    anchor='\t\t\t\tprintk("%s, '+message+'\\n", __func__, j);\n\t\t\t\tbreak;'
    if f.count(anchor)!=1:raise SystemExit('Changed flush timeout')
    f=f.replace(anchor,anchor.rsplit('\n',1)[0]+'\n\t\t\t\t*is_pretbtt_int = FALSE;\n\t\t\t\treturn;',1)
anchor='\tRTMP_IO_READ32(pAd, ARB_BCNQCR0, &temp);//re-enable bcn_start'
if f.count(anchor)!=1:raise SystemExit('Changed final beacon restart')
f=f.replace(anchor,'''\t/* Recheck the same eligibility used by beacon updates after both flushes.
\t * This does not serialize with a simultaneous BSS close. */
\tif (!BeaconTransmitRequired(pAd, apidx, pMbss)) {
\t\t*is_pretbtt_int = FALSE;
\t\treturn;
\t}
'''+anchor,1)
finish='''\tRTMP_IO_READ32(pAd, ARB_BCNQCR0, &temp);//re-enable bcn_start
\ttemp = temp | val;
\tRTMP_IO_WRITE32(pAd, ARB_BCNQCR0, temp);

\tpMbss->bcn_buf.bcn_state = BCN_TX_IDLE;'''
if f.count(finish)!=1:raise SystemExit('Changed recovery final RMW')
f=f.replace(finish,'''\t/* Close intent and the final restart share the beacon ring lock. */
\tRTMP_SEM_LOCK(&pAd->BcnRingLock);
\tif (!pMbss->bcn_buf.bBcnSntReq ||
\t    (apidx > 0 && (!pMbss->wdev.if_dev ||
\t     !RTMP_OS_NETDEV_STATE_RUNNING(pMbss->wdev.if_dev)))) {
\t\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);
\t\t*is_pretbtt_int = FALSE;
\t\treturn;
\t}
\tRTMP_IO_READ32(pAd, ARB_BCNQCR0, &temp);//re-enable bcn_start
\ttemp = temp | val;
\tRTMP_IO_WRITE32(pAd, ARB_BCNQCR0, temp);
\tpMbss->bcn_buf.bcn_state = BCN_TX_IDLE;
\tRTMP_SEM_UNLOCK(&pAd->BcnRingLock);''',1)
guard='''if (RTMP_TEST_FLAG(pAd, fRTMP_ADAPTER_NIC_NOT_EXIST | fRTMP_ADAPTER_HALT_IN_PROGRESS |
                       fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET)
#ifdef RTMP_MAC_PCI
    || pAd->bPCIclkOff
#endif
    ) { *is_pretbtt_int = FALSE; return; }
'''
anchor='\tpMbss = &pAd->ApCfg.MBSSID[apidx];'
if f.count(anchor)!=1:raise SystemExit('Changed BSS lookup')
f=f.replace(anchor,guard+anchor,1)
lines=[]
for line in f.splitlines(keepends=True):
    if line.lstrip().startswith(('RTMP_IO_READ32(','RTMP_IO_WRITE32(')):
        if 'ARB_BCNQCR0' in line:
            lock_guard=guard.replace('*is_pretbtt_int = FALSE; return;',
                                     'RTMP_SEM_UNLOCK(&pAd->BcnRingLock); *is_pretbtt_int = FALSE; return;')
            lines.extend([lock_guard,line,lock_guard])
        else:
            lines.extend([guard,line,guard])
    else:lines.append(line)
f=''.join(lines)
prefix=r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef void VOID;
typedef unsigned int UINT32;
typedef int INT;
typedef int BOOLEAN;
typedef struct {void *if_dev;} WDEV;
typedef struct {struct {int bcn_state,bBcnSntReq;} bcn_buf;WDEV wdev;unsigned int WriteBcnDoneTime[1];int timer_loop,bcn_not_idle_time,bcn_recovery_num;} BSS_STRUCT;
typedef struct {int flags,pse_reset_flag,bPCIclkOff,bcn_reset_en,bcn_not_idle_tx_dma_busy;
 unsigned int bcn_didx_val,dma_force_reset_count;struct {unsigned int hw_didx_addr;} BcnRing;
 struct {int BssidNum;BSS_STRUCT MBSSID[3];} ApCfg;struct {int BeaconPeriod;} CommonCfg;int BcnRingLock;} RTMP_ADAPTER;
#define RTMP_MAC_PCI 1
#define DMA_RESET_SUPPORT 1
#define TXRXCR_DEBUG_SUPPORT 1
#define TRUE 1
#define FALSE 0
#define BCN_TX_DMA_DONE 1
#define BCN_TX_IDLE 0
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 2
#define fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET 4
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define RTMP_OS_NETDEV_STATE_RUNNING(dev) (dev_running)
#define DBGPRINT(level,args) ((void)0)
#define printk(...) ((void)0)
#define OS_WAIT(n) ((void)(n))
#define ARB_BCNQCR0 0x100U
#define ARB_BCNQCR1 0x104U
#define MT_WPDMA_GLO_CFG 0x300U
static int check_point_num,pse_rst_counter,mode,start_writes,flush_writes,pse_writes,txrx_calls,locks,unlocks;
static unsigned int start_value,flush_value;
static RTMP_ADAPTER *current_ad;
static int dev_running;
#define RTMP_SEM_LOCK(lock) do {assert(!*(lock));*(lock)=1;locks++;if(mode==16)current_ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;} while(0)
#define RTMP_SEM_UNLOCK(lock) do {assert(*(lock));*(lock)=0;unlocks++;} while(0)
static int BeaconTransmitRequired(RTMP_ADAPTER *ad,int idx,BSS_STRUCT *bss){
 (void)ad;return bss->bcn_buf.bBcnSntReq && (idx==0 || dev_running);
}
static void DumpBcnQMessage(RTMP_ADAPTER *ad,int idx){(void)ad;(void)idx;}
static void AsicGetTsfTime(RTMP_ADAPTER *ad,unsigned int *hi,unsigned int *lo){(void)ad;*hi=0;*lo=10000;}
static void set_get_fid(RTMP_ADAPTER *ad,const char *s){(void)ad;(void)s;}
static void SetTxRxCr_Proc(RTMP_ADAPTER *ad,const char *s){(void)ad;(void)s;txrx_calls++;}
static void write_reg(unsigned int address,unsigned int value){
 if(address==ARB_BCNQCR0){start_writes++;start_value=value;}
 else if(address==ARB_BCNQCR1){flush_writes++;flush_value=value;}
 else {assert(address==0x21c08U);pse_writes++;}
}
static unsigned int read_reg(unsigned int address){
 if(address==MT_WPDMA_GLO_CFG){if(mode==13)current_ad->bPCIclkOff=1;return 2;}
 if(address==current_ad->BcnRing.hw_didx_addr)return 7;
 if(address==ARB_BCNQCR0){if(mode==10)current_ad->bPCIclkOff=1;return start_value;}
 if(address==ARB_BCNQCR1){if(mode==8)current_ad->bPCIclkOff=1;return mode==1?flush_value:0;}
 if(address==0x21c08U){if(mode==9)current_ad->flags=2;return mode==2?0x80000000U:0;}
 assert(address==0x21c0cU);
 if(mode==11)current_ad->ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=0;
 if(mode==12)dev_running=0;
 return 0;
}
#define RTMP_IO_WRITE32(ad,address,value) ((void)(ad),write_reg(address,value))
#define RTMP_IO_READ32(ad,address,value) ((void)(ad),*(value)=read_reg(address))
'''
tail=r'''
int main(void){
 RTMP_ADAPTER ad;BOOLEAN proceed;
 for(mode=0;mode<18;mode++){
  memset(&ad,0,sizeof(ad));ad.ApCfg.BssidNum=3;ad.CommonCfg.BeaconPeriod=1;
  ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=1;ad.ApCfg.MBSSID[2].bcn_not_idle_time=2;
  ad.ApCfg.MBSSID[2].bcn_buf.bBcnSntReq=1;
  ad.ApCfg.MBSSID[2].wdev.if_dev=&ad;dev_running=1;
  ad.BcnRing.hw_didx_addr=0x304U;
  if(mode>=13&&mode<=15){ad.ApCfg.MBSSID[0].bcn_buf.bcn_state=0;ad.bcn_reset_en=mode!=15;
    ad.bcn_not_idle_tx_dma_busy=mode!=15;ad.bcn_didx_val=7;}
  check_point_num=mode==13||mode==14?4:mode==15?6:0;
  pse_rst_counter=0;txrx_calls=locks=unlocks=0;
  start_writes=flush_writes=pse_writes=0;start_value=0x10000U;proceed=TRUE;
  if(mode==5)ad.flags=1;
  if(mode==17)ad.flags=fRTMP_ADAPTER_DISABLE_DEQUEUEPACKET;
  if(mode==7)ad.bPCIclkOff=1;
  current_ad=&ad;
  APCheckBcnQHandler(mode==6?NULL:&ad,mode==3?-1:mode==4?3:mode>=13&&mode<=15?0:2,&proceed);
  if(mode==0){
   assert(proceed&&start_writes==1&&flush_writes==1&&pse_writes==1);
   assert(start_value==(0x10000U|(1U<<17))&&ad.ApCfg.MBSSID[2].bcn_buf.bcn_state==0);
  }else{
   assert(!proceed&&!start_writes&&ad.ApCfg.MBSSID[2].bcn_buf.bcn_state==1);
   if(mode==1)assert(flush_writes==1&&!pse_writes);
   if(mode==2)assert(flush_writes==1&&pse_writes==1);
   if((mode>=3&&mode<=7)||mode==17)assert(!flush_writes&&!pse_writes);
   if(mode==8)assert(flush_writes==1&&!pse_writes);
   if(mode==9||mode==10||mode==11||mode==12||mode==16)assert(flush_writes==1&&pse_writes==1);
   if(mode>=13&&mode<=15){
    assert(!flush_writes&&!pse_writes&&ad.ApCfg.MBSSID[0].bcn_buf.bcn_state==0);
    if(mode==13)assert(ad.bPCIclkOff&&!ad.dma_force_reset_count&&!txrx_calls);
    if(mode==14)assert(ad.dma_force_reset_count==1&&ad.pse_reset_flag&&ad.bcn_didx_val==255);
    if(mode==15)assert(txrx_calls==1&&!ad.dma_force_reset_count);
   }
  }
  assert(!ad.BcnRingLock&&locks==unlocks);
  if(mode==16)assert(locks==1&&unlocks==1);
 }
 puts("PASS actual beacon recovery candidate: timeout/device loss/closed/reset-gated BSS; active DMA_RESET and TXRXCR branches; final lock balanced");
 return 0;
}
'''
if a.input.read_bytes()!=d:raise SystemExit('Input changed')
a.candidate.write_text(s[:start]+f+s[end:],encoding='utf-8')
a.fixture.write_text(prefix+f+tail,encoding='utf-8')
