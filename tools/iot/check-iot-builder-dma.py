#!/usr/bin/env python3
"""Execute candidate producer binding: exclusive IoT builder and pinned DMA check."""
import argparse,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
s=(here/'check-beacon-producer-kernel.c').read_text()
s=s.replace('typedef int INT;','typedef int INT;typedef unsigned UINT32;')
s=s.replace(' int BcnRingLock, wr_iot_beacon_wait;',' int mt,BcnRingLock, wr_iot_beacon_wait;')
anchor='#include "beacon-producer-kernel.h"'
s=s.replace(anchor,'''static int dma_result,checks,revoke_during_check,change_count;
#define IS_MT7603(ad) ((ad)->mt)
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *ad,UINT32 bss);
'''+(a.driver/'include/wr-iot-beacon-producer-kernel.h').read_text()+'''
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *ad,UINT32 bss){
 struct wr_iot_beacon_producer_ticket racing={0};
 assert(!locked&&bss==2&&ad->wr_iot_beacon_gates[2].active==1);checks++;
 /* Another builder attempts admission while the first snapshot is unlocked. */
 assert(!wr_iot_bcn_producer_begin(ad,2,&racing)&&!racing.active);
 assert(checks==1&&!locked);
 if(revoke_during_check)assert(wr_iot_beacon_gate_revoke(&ad->wr_iot_beacon_gates[2],1));
 if(change_count)ad->ApCfg.BssidNum=4;
 return dma_result;
}
''')
anchor=' puts("PASS kernel adapter binding:'
i=s.index(anchor)
s=s[:i]+''' ad.mt=1;
 for(int fault=0;fault<5;fault++){
  struct wr_iot_beacon_producer_ticket pin={0},other={0};
  wr_iot_beacon_gate_init(&ad.wr_iot_beacon_gates[2]);
  assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[2],1));
  ad.ApCfg.BssidNum=3;change_count=fault==4;
  int prior_wakes=wakes;
  dma_result=fault==1?1:fault==2?-1:0;revoke_during_check=fault==3;checks=0;
  assert(wr_iot_bcn_producer_begin(&ad,2,&pin)==(fault==0));
  assert(checks==1&&!locked);
  if(!fault){
   assert(!wr_iot_bcn_producer_begin(&ad,2,&other)&&checks==1);
   wr_iot_bcn_producer_end(&ad,2,&pin);
  }
  assert(!ad.wr_iot_beacon_gates[2].active&&!pin.active);
  assert(wakes==prior_wakes+1);
 }
'''+s[i:]
with tempfile.TemporaryDirectory(prefix='wr-iot-builder-dma-') as d:
 src=Path(d)/'t.c';exe=Path(d)/'t';src.write_text(s)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS actual candidate IoT builder: exclusive pin, DMA busy/unknown refusal, close race, Guest original behavior; no RF proof')
