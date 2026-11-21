#!/usr/bin/env python3
"""Compose actual TxS callback and actual producer admission, with injected DMA.
Checks buffer-builder admission despite stale IDLE; does not prove RF retirement.
"""
import argparse,ast,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('driver',type=Path);a=p.parse_args()
# Reuse the reviewed callback ABI fixture, without copying its function body.
tree=ast.parse(Path(__file__).with_name('check-beacon-txs-stop.py').read_text())
pre=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='pre' for t in n.targets))
pre=pre.replace('unsigned BssidNum;', 'UCHAR BssidNum;')
pre=pre.replace('int bcn_state;', 'int bcn_state,bBcnSntReq;')
pre=pre.replace('int OpMode,BcnRingLock;', 'int mt,OpMode,BcnRingLock,wr_iot_beacon_wait;struct wr_iot_beacon_producer_gate wr_iot_beacon_gates[3];')
pre='#include "wr-iot-beacon-producer-gate.h"\n'+pre
source=(a.driver/'tx_rx/txs.c').read_text();sig='INT32 BcnTxSHandler(RTMP_ADAPTER *pAd, CHAR *Data, UINT32 Priv)'
assert source.count(sig)==1;start=source.index(sig);callback=source[start:source.index('\n}',start)+2]
extra=r'''
#define WR_IOT_HOST_TEST 1
#define WDEV_NUM_MAX 3
#define RTMP_SEM_LOCK(p) do{assert(!*(p));*(p)=1;}while(0)
#define RTMP_SEM_UNLOCK(p) do{assert(*(p));*(p)=0;}while(0)
#define wake_up_all(p) ((void)(p))
#define in_atomic() 0
#define irqs_disabled() 0
#define READ_ONCE(x) (x)
#define msecs_to_jiffies(x) (x)
#define wait_event_timeout(q,c,t) ((void)(q),(void)(t),(c)?1:0)
#define IS_MT7603(ad) ((ad)->mt)
typedef int INT;
static int dma_result,checks;
static int WrBeaconTxSOutstanding(RTMP_ADAPTER *ad,UINT32 bss){
 assert(bss==2&&!ad->BcnRingLock&&ad->wr_iot_beacon_gates[2].active==1);return 0;
}
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *ad,UINT32 bss){
 assert(bss==2&&!ad->BcnRingLock&&ad->wr_iot_beacon_gates[2].active==1);
 checks++;return dma_result;
}
'''
main=r'''
int main(void){
 RTMP_ADAPTER ad={.mt=1,.OpMode=OPMODE_AP,.ApCfg.BssidNum=3};
 TXS_STRUC report={0};
 for(int mode=-1;mode<=1;mode++){
  struct wr_iot_beacon_producer_ticket pin={0};
  wr_iot_beacon_gate_init(&ad.wr_iot_beacon_gates[2]);
  assert(wr_iot_beacon_gate_open(&ad.wr_iot_beacon_gates[2],1));
  ad.ApCfg.MBSSID[2].bcn_buf.bcn_state=1;
  assert(BcnTxSHandler(&ad,(CHAR *)&report,2)==0);
  assert(ad.ApCfg.MBSSID[2].bcn_buf.bcn_state==BCN_TX_IDLE);
  dma_result=mode;checks=0;
  assert(wr_iot_bcn_producer_begin(&ad,2,&pin)==(mode==0));
  assert(checks==1&&!ad.BcnRingLock);
  if(mode==0)wr_iot_bcn_producer_end(&ad,2,&pin);
  assert(!pin.active&&!ad.wr_iot_beacon_gates[2].active);
 }
 puts("PASS actual TxS+builder composition: stale IDLE cannot admit builder with busy/unknown DMA; zero DMA permits pinned builder, not RF acceptance");
}
'''
header=(a.driver/'include/wr-iot-beacon-producer-kernel.h').read_text()
assert 'WrBeaconDmaOutstanding(ad' in header, 'Expected final DMA-guarded API candidate'
with tempfile.TemporaryDirectory(prefix='wr-iot-txs-builder-') as d:
 c=Path(d)/'t.c';exe=Path(d)/'t';c.write_text(pre+callback+extra+header+main)
 for flags in [[],['-DDBG']]:
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-Wno-unused-variable','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.driver/'include'),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
