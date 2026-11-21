#!/usr/bin/env python3
"""Execute generated MT7603 channel wrapper with injected MCU outcomes."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
a = p.parse_args()
s = (a.candidate / 'chips/mt7603.c').read_text()
start = s.index('static void mt7603_switch_channel(')
body = s[start:s.index('\n}\n', start) + 3]
assert 'wr_iot_mcu_config_fail(pAd)' in body
prefix = r'''
#include <assert.h>
#include <stdio.h>
#define MT7603 1
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define BW_20 0
#define NDIS_STATUS_SUCCESS 0
#define DBGPRINT(...) ((void)0)
typedef unsigned char UCHAR;
typedef int BOOLEAN;
typedef struct adapter {
 unsigned wr_iot_boot_active,wr_iot_boot_failed;
 struct {void (*ChipSwitchChannel)(struct adapter *,UCHAR,BOOLEAN);} chipOps;
 struct {unsigned hif_type;} chipCap;
 struct {unsigned BBPCurrentBW,Channel,TxStream,RxStream;} CommonCfg;
 struct {unsigned Channel;} LatchRfRegs;
} RTMP_ADAPTER;
static unsigned mode,channels,powers,failures,expected_bw;
static int CmdChannelSwitch(RTMP_ADAPTER *ad,unsigned control,unsigned central,
 unsigned bw,unsigned tx,unsigned rx){
 assert(control==(bw==BW_20?6:3)&&central==6&&bw==expected_bw&&tx==2&&rx==1);
 channels++;if(mode==2)ad->wr_iot_boot_failed=1;return mode==1?1:0;
}
static void CmdSetTxPowerCtrl(RTMP_ADAPTER *ad,unsigned channel){
 assert(channel==6);powers++;if(mode==3)ad->wr_iot_boot_failed=1;
}
static int wr_iot_mcu_config_fail(RTMP_ADAPTER *ad){
 failures++;ad->wr_iot_boot_failed=1;return 1;
}
'''
tail = r'''
int main(void){
 for(unsigned active=0;active<2;active++)
 for(unsigned bw=0;bw<2;bw++)
 for(mode=0;mode<5;mode++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=active;
  ad.wr_iot_boot_failed=mode==4;ad.CommonCfg.BBPCurrentBW=bw;
  ad.CommonCfg.Channel=3;ad.CommonCfg.TxStream=2;ad.CommonCfg.RxStream=1;
  ad.LatchRfRegs.Channel=11;channels=powers=failures=0;expected_bw=bw;
  mt7603_switch_channel(&ad,6,1);
  assert(channels==(!active||mode!=4));
  assert(powers==(!active||mode==0||mode==3));
  assert(failures==(active&&mode==1));
  assert(ad.LatchRfRegs.Channel==(!active||mode==0?6:11));
 }
 puts("PASS channel latch: private command failure/preexisting failure preserves old latch and suppresses later commands; ordinary SDK behavior and both bandwidth branches preserved; MCU injected");
}
'''
outer_path = a.candidate / 'hw_ctrl/cmm_asic_mt.c'
outer_source = outer_path.read_text()
outer_start = outer_source.index('VOID AsicSwitchChannel(')
outer = outer_source[outer_start:outer_source.index('\n}\n', outer_start) + 3]
caller = 'if(pAd->wr_iot_boot_active&&pAd->wr_iot_boot_failed)return;' in outer
assert caller, 'Expected installed channel-caller failure guard'
if caller:
    body += r'''
#define VOID void
#define UINT32 unsigned
#define HIF_MT 1
#define RMAC_CHFREQ 0
#define RTMP_TEST_FLAG(...) 0
static unsigned reads,writes,agc;
#define RTMP_IO_READ32(ad,reg,out) (reads++,*(out)=0)
#define RTMP_IO_WRITE32(ad,reg,value) ((void)(value),writes++)
#define RTMPSetAGCInitValue(ad,bw) ((void)(bw),agc++)
''' + outer
    tail = tail.replace(' puts("PASS channel latch:', r'''
 for(unsigned active=0;active<2;active++)
 for(unsigned scan=0;scan<2;scan++)
 for(mode=0;mode<6;mode++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=active;
  ad.wr_iot_boot_failed=mode==4;ad.CommonCfg.BBPCurrentBW=0;
  ad.CommonCfg.Channel=3;ad.CommonCfg.TxStream=2;ad.CommonCfg.RxStream=1;
  ad.LatchRfRegs.Channel=11;ad.chipCap.hif_type=HIF_MT;
  ad.chipOps.ChipSwitchChannel=mode==5?0:mt7603_switch_channel;
  channels=powers=failures=reads=writes=agc=0;expected_bw=0;
  AsicSwitchChannel(&ad,6,scan);
  unsigned follow=!active||mode==0;
  assert(reads==follow&&writes==follow&&agc==follow);
  if(active&&mode==5)assert(failures==1&&ad.wr_iot_boot_failed&&!channels&&!powers);
 }
 puts("PASS outer channel caller: real chip wrapper failure suppresses register/AGC side effects; missing callback fails private owner; ordinary SDK route preserved");
 puts("PASS channel latch:''')
with tempfile.TemporaryDirectory(prefix='wr-iot-channel-latch-') as temp:
    source = Path(temp) / 'check.c'
    exe = Path(temp) / 'check'
    source.write_text(prefix + body + tail)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Wno-unused-parameter',
                    '-Werror', '-fsanitize=address,undefined', str(source),
                    '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
