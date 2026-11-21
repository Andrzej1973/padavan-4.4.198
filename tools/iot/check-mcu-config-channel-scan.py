#!/usr/bin/env python3
"""Execute generated automatic-channel loop with injected switch failures."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
a = p.parse_args()
s = (a.candidate / 'ap/ap_autoChSel.c').read_text()
start = s.index('UCHAR APAutoSelectChannel(')
body = s[start:s.index('\n}\n', start) + 3]
assert body.count('if(pAd->wr_iot_boot_active&&pAd->wr_iot_boot_failed)return 0;') == 2
prefix = r'''
#include <assert.h>
#include <stdio.h>
#define MT7603 1
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define TRUE 1
#define ChannelAlgRandom 0
typedef unsigned char UCHAR;
typedef unsigned long ULONG;
typedef unsigned ChannelSel_Alg;
typedef struct {
 unsigned wr_iot_boot_active,wr_iot_boot_failed,ChannelListNum;
 struct {unsigned IsABand;} info,*pChannelInfo;
 struct {UCHAR Channel;} ChannelList[13];
 struct {unsigned current_channel_index,AutoChannel_Channel;} ApCfg;
} RTMP_ADAPTER;
static unsigned initialized,switched,locked,busy,waited,updated,selected,fail_at;
static void APAutoChannelInit(RTMP_ADAPTER *ad){(void)ad;initialized++;}
static UCHAR SelectClearChannelRandom(RTMP_ADAPTER *ad){(void)ad;selected++;return 44;}
static void AsicSwitchChannel(RTMP_ADAPTER *ad,UCHAR channel,unsigned scan){
 assert(scan&&channel==switched+1);switched++;
 if(switched==fail_at)ad->wr_iot_boot_failed=1;
}
static void AsicLockChannel(RTMP_ADAPTER *ad,UCHAR channel){(void)ad;(void)channel;locked++;}
static unsigned AsicGetChBusyCnt(RTMP_ADAPTER *ad,unsigned index){(void)ad;assert(!index);busy++;return 0;}
static void OS_WAIT(ULONG interval){assert(interval==200);waited++;}
static void UpdateChannelInfo(RTMP_ADAPTER *ad,unsigned i,ChannelSel_Alg alg){
 (void)ad;(void)alg;assert(i==updated);updated++;
}
static UCHAR SelectBestChannel(RTMP_ADAPTER *ad,ChannelSel_Alg alg){
 (void)ad;(void)alg;selected++;return 6;
}
'''
tail = r'''
int main(void){
 for(unsigned active=0;active<2;active++)
 for(unsigned n=11;n<=13;n+=2)
 for(unsigned fault=0;fault<=n+1;fault++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=active;ad.ChannelListNum=n;
  ad.pChannelInfo=&ad.info;ad.ApCfg.current_channel_index=99;
  ad.ApCfg.AutoChannel_Channel=99;for(unsigned i=0;i<n;i++)ad.ChannelList[i].Channel=i+1;
  fail_at=fault;ad.wr_iot_boot_failed=fault==n+1;
  initialized=switched=locked=busy=waited=updated=selected=0;
  unsigned result=APAutoSelectChannel(&ad,1);
  unsigned failed=active&&fault;
  unsigned complete=failed?(fault==n+1?0:fault-1):n;
  assert(result==(failed?0:6));
  assert(initialized==!(active&&fault==n+1));
  assert(switched==(failed?(fault==n+1?0:fault):n));
  assert(locked==complete&&busy==complete&&waited==complete&&updated==complete);
  assert(selected==!failed);
  assert(ad.ApCfg.current_channel_index==(complete?complete-1:99));
  assert(ad.ApCfg.AutoChannel_Channel==(complete?complete:99));
 }
 puts("PASS automatic-channel loop: every failure position and preexisting refusal stop private statistics/wait/selection; all 11/13 channels retained on success and ordinary SDK path; switch injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-iot-channel-scan-') as temp:
    source = Path(temp) / 'check.c'
    exe = Path(temp) / 'check'
    source.write_text(prefix + body + tail)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(source), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
