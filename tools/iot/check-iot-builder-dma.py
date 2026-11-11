#!/usr/bin/env python3
"""Execute candidate producer binding: exclusive IoT builder and pinned DMA check."""
import argparse,ast,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',nargs='?',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
if a.driver:
 header=(a.driver/'include/wr-iot-beacon-producer-kernel.h').read_text()
 periodic=(a.driver/'ap/ap_connect.c').read_text()
 assert periodic.count('if (wr_iot_bcn_periodic_ready(pAd, apidx, &ticket))')==1
else:
 header=(here/'beacon-producer-kernel.h').read_text()
 tree=ast.parse((here/'prepare-driver-api.py').read_text())
 for node in tree.body:
  if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call):
   call=node.value
   if isinstance(call.func,ast.Name) and call.func.id=='one' and isinstance(call.args[0],ast.Constant) and ast.literal_eval(call.args[0])=='include/wr-iot-beacon-producer-kernel.h':
    old,new=map(ast.literal_eval,call.args[1:]);assert header.count(old)==1
    header=header.replace(old,new,1)
s=(here/'check-beacon-producer-kernel.c').read_text()
s=s.replace('typedef int INT;','typedef int INT;typedef unsigned UINT32;')
s=s.replace(' int BcnRingLock, wr_iot_beacon_wait;',' int mt,BcnRingLock, wr_iot_beacon_wait;')
s=s.replace('int bBcnSntReq;', 'int bBcnSntReq,bcn_state;')
anchor='#include "beacon-producer-kernel.h"'
s=s.replace(anchor,'''static int dma_result,txs_result,checks,revoke_during_check,change_count,periodic_count_change;
#define BCN_TX_IDLE 0
#define IS_MT7603(ad) ((ad)->mt)
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *ad,UINT32 bss);
static int WrBeaconTxSOutstanding(RTMP_ADAPTER *ad,UINT32 bss){
 assert(!locked&&bss==2&&ad->wr_iot_beacon_gates[2].active==1);if(periodic_count_change)ad->ApCfg.BssidNum=4;return txs_result;
}
'''+header+'''
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
 for(int fault=0;fault<9;fault++){
  struct wr_iot_beacon_producer_ticket pin={0},other={0};
  wr_iot_beacon_gate_init(&ad.wr_iot_beacon_gates[2]);
  assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[2],1));
  ad.ApCfg.BssidNum=3;change_count=fault==4;
  int prior_wakes=wakes;
  dma_result=fault==1?1:fault==2?-1:0;revoke_during_check=fault==3;checks=0;
  periodic_count_change=fault==8;
  txs_result=fault==5?1:fault==6?-1:0;
  ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=fault==7?1:BCN_TX_IDLE;
  assert(wr_iot_bcn_producer_begin(&ad,2,&pin)==(fault==0||fault>=5));
  assert(checks==1&&!locked);
  if(!fault||fault>=5){
   assert(wr_iot_bcn_periodic_ready(&ad,2,&pin)==(fault==0));
   if(fault!=8)assert(!wr_iot_bcn_producer_begin(&ad,2,&other)&&checks==1);
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
print('PASS actual candidate IoT builder: exclusive pin, DMA busy/unknown refusal, periodic TxS busy/unknown/non-IDLE refusal, close race, Guest original behavior; no RF proof')
