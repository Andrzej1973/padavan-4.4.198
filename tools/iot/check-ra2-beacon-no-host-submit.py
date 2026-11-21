#!/usr/bin/env python3
"""Run actual composed MT lower C with injected packet validator and hardware."""
import argparse
from pathlib import Path
import runpy
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--archive', required=True, type=Path)
a = p.parse_args()
here = Path(__file__).resolve().parent
old = runpy.run_path(str(here / 'check-tracked-beacon-reservation.py'))
policy = runpy.run_path(str(here / 'ra2-beacon-no-host-submit.py'))
with tempfile.TemporaryDirectory(prefix='wr-no-host-lower-c-') as scratch:
    root = Path(scratch)
    original = old['predecessor'](root, a.archive)
    source = policy['compose'](old['POLICY']['compose'](original))
    try:
        policy['compose'](source)
    except ValueError:
        pass
    else:
        raise AssertionError('Repeated lower composition accepted')
    c = old['fixture_text'](source)
    anchor = 'typedef struct {UINT8 pid;UINT32 generation;} WR_BCN_TXS_RESERVATION;'
    assert c.count(anchor) == 1
    c = c.replace(anchor, '#include "beacon-producer-gate.h"\n'
        'typedef struct {UINT8 pid;UINT32 generation;struct wr_iot_beacon_producer_ticket producer;} WR_BCN_TXS_RESERVATION;')
    position = c.index('INT32 RT28xx_UpdateBeaconToAsic(')
    stubs = r'''
static int dma_result,packet_ok;
#define MAX_BEACON_SIZE 16U
static int WrBeaconDmaOutstanding(RTMP_ADAPTER *a,unsigned b)
{assert(a&&!held&&b==2);return dma_result;}
static int wr_iot_ra2_no_host_packet(RTMP_ADAPTER *a,PNDIS_PACKET *p,
 const struct wr_iot_beacon_producer_ticket *t,const void *data,unsigned len,int dma)
{assert(a&&p&&data&&len&&held);return packet_ok&&dma==0&&t->active&&t->generation==17;}
'''
    c = c[:position] + stubs + c[position:]
    position = c.index('int main(void){')
    c = c[:position] + r'''
int main(void){
 for(int fault=0;fault<10;fault++){
  reset();packet_ok=1;dma_result=0;WR_BCN_TXS_RESERVATION r={0};
  r.producer.generation=17;r.producer.active=1;
  if(fault==1)r.producer.active=0;
  if(fault==2)dma_result=1;
  if(fault==3)packet_ok=0;
  if(fault==4)ad.BcnRing.TxSwFreeIdx=1;
  if(fault==5)hal_result=-1;
  if(fault==6)r.producer.generation=16;
  if(fault==7)ad.ApCfg.BssidNum=4;
  if(fault==8)ad.chipCap.tx_hw_hdr_len=17;
  assert(RT28xx_UpdateBeaconToAsic(&ad,2,fault==9?~0U:8,0,r)==(fault==0?0:-1));
  assert(!held&&locks==unlocks&&!cancels&&publications==(fault==0));
  assert(kicks==(fault==0||fault==5));
  if(fault>=8)assert(!pkt.len&&!locks);
 }
 reset();packet_ok=1;dma_result=0;WR_BCN_TXS_RESERVATION boundary={0};
 boundary.producer.generation=17;boundary.producer.active=1;
 assert(!RT28xx_UpdateBeaconToAsic(&ad,2,12,0,boundary)&&pkt.len==16&&kicks==1);
 reset();packet_ok=1;dma_result=0;
 assert(RT28xx_UpdateBeaconToAsic(&ad,2,13,0,boundary)==-1&&!pkt.len&&!locks&&!kicks);
 reset();packet_ok=0;dma_result=-1;WR_BCN_TXS_RESERVATION r={0};
 assert(!RT28xx_UpdateBeaconToAsic(&ad,1,8,0,r)&&kicks==1&&publications==1);
 puts("PASS actual transformed lower C: original ticket/stale/missing, DMA, packet guard, ring/HAL refusal and Guest path; packet validator and hardware injected");
 return 0;
}
'''
    src = root / 'lower.c'
    exe = root / 'lower'
    src.write_text(c)
    subprocess.run(['gcc', '-std=gnu11', '-Wall', '-Wextra', '-Werror', '-O2',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    '-I'+str(here), str(src), '-o', str(exe)], check=True)
    subprocess.run([str(exe)], check=True)
