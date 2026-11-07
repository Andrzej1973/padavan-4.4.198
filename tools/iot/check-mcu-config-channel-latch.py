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
typedef struct {
 unsigned wr_iot_boot_active,wr_iot_boot_failed;
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
with tempfile.TemporaryDirectory(prefix='wr-iot-channel-latch-') as temp:
    source = Path(temp) / 'check.c'
    exe = Path(temp) / 'check'
    source.write_text(prefix + body + tail)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Wno-unused-parameter',
                    '-Werror', '-fsanitize=address,undefined', str(source),
                    '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
