#!/usr/bin/env python3
"""Execute the actual beacon TxS callback; stopped safety is not reopen safety."""
import argparse
import subprocess
import tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('driver',type=Path)
a=p.parse_args()
s=(a.driver/'tx_rx/txs.c').read_text()
anchor='INT32 BcnTxSHandler(RTMP_ADAPTER *pAd, CHAR *Data, UINT32 Priv)'
if s.count(anchor)!=1:raise SystemExit('Changed callback signature')
start=s.index(anchor);body=s[start:s.index('\n}',start)+2]
pre=r'''
#include <assert.h>
#include <string.h>
#include <stdio.h>
#define CONFIG_AP_SUPPORT 1
#define RTMP_MAC_PCI 1
#define MT_MAC 1
#define OPMODE_AP 1
#define BCN_TX_STOP 3
#define BCN_TX_IDLE 0
#define MAX_TIME_RECORD 4
#define RT_DEBUG_INFO 0
#define DBGPRINT(level,args) do{(void)(level);}while(0)
typedef int INT32;typedef unsigned UINT32;typedef char CHAR;
typedef unsigned char UCHAR;typedef unsigned long ULONG;
typedef struct {int unused;} TXS_STRUC;
typedef struct {struct {int bcn_state;} bcn_buf;unsigned bcn_not_idle_time,timer_loop;} BSS_STRUCT;
typedef struct {int OpMode,BcnRingLock;struct {unsigned BssidNum;BSS_STRUCT MBSSID[3];} ApCfg;} RTMP_ADAPTER;
#define MAX_MBSSID_NUM(ad) 3U
#define RTMP_IRQ_LOCK(lock,flags) do{(flags)=0;assert(!*(lock));*(lock)=1;}while(0)
#define RTMP_IRQ_UNLOCK(lock,flags) do{(void)(flags);assert(*(lock));*(lock)=0;}while(0)
'''
post=r'''
int main(void){
 RTMP_ADAPTER ad={.OpMode=OPMODE_AP,.ApCfg.BssidNum=3};TXS_STRUC report={0};
 ad.ApCfg.MBSSID[2]=(BSS_STRUCT){.bcn_buf.bcn_state=BCN_TX_STOP,.bcn_not_idle_time=9,.timer_loop=2};
 BSS_STRUCT before=ad.ApCfg.MBSSID[2];
 assert(BcnTxSHandler(&ad,(CHAR *)&report,2)==-1);
 assert(!memcmp(&before,&ad.ApCfg.MBSSID[2],sizeof(before))&&!ad.BcnRingLock);
 assert(BcnTxSHandler(&ad,(CHAR *)&report,3)==-1&&!ad.BcnRingLock);
 assert(BcnTxSHandler(&ad,(CHAR *)&report,~0U)==-1&&!ad.BcnRingLock);
 /* Negative witness: identical uncorrelated report can mutate reopened state. */
 ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=1;
 assert(!BcnTxSHandler(&ad,(CHAR *)&report,2));
 assert(ad.ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_IDLE);
 assert(!ad.ApCfg.MBSSID[2].bcn_not_idle_time&&ad.ApCfg.MBSSID[2].timer_loop==3);
 puts("PASS actual callback STOP/bounds immutability; negative reopened-state witness. No hardware delivery/RF proof.");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-txs-stop-') as tmp:
 src=Path(tmp)/'test.c';exe=Path(tmp)/'test';src.write_text(pre+body+post)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-variable','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
