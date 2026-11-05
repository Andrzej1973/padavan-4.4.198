#!/usr/bin/env python3
"""Run the real bounded drain coordinator with injected MMIO and RX/PSE observations."""
import argparse
from pathlib import Path
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
a = p.parse_args()
fixture = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef int INT32;typedef int INT;typedef uint32_t UINT32;
typedef struct {unsigned flags;} RTMP_ADAPTER;
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_SUCCESS 0
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
#define MT_WPDMA_GLO_CFG 1
#define TX_DMA_EN 1u
#define TX_DMA_BUSY 2u
#define RX_DMA_EN 4u
#define RX_DMA_BUSY 8u
static unsigned hardware_cfg,mode,calls,reads,delays,owned,atomic_context,irq_off;
#define in_atomic() atomic_context
#define irqs_disabled() irq_off
#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))
#define RTMP_IO_READ32(ad,reg,out) do{assert(ad);assert((reg)==1);reads++;*(out)=hardware_cfg;}while(0)
#define RtmpusecDelay(n) do{assert((n)==1000);delays++;}while(0)
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(ad);return owned;}
static int wr_iot_mcu_boot_rx_discard_batch(RTMP_ADAPTER *ad,unsigned *empty){
 assert(ad);calls++;*empty=mode==3?0:mode==4&&calls==2?0:1;
 if(mode==6)owned=0;
 return mode==2?1:0;
}
static int wr_iot_boot_pse_snapshot(RTMP_ADAPTER *ad){
 assert(ad);if(mode==1)return -1;if(mode==5)return 0;
 if(mode==7&&calls<4)return 0;
 return 1;
}
'''+(a.candidate/'include/wr-iot-mcu-boot-pse-drain.inc').read_text()+r'''
static void fresh(void){hardware_cfg=RX_DMA_EN;mode=calls=reads=delays=atomic_context=irq_off=0;owned=1;}
int main(void){
 RTMP_ADAPTER ad={0};
 for(unsigned live=0;live<2;live++){
  fresh();hardware_cfg=live?RX_DMA_EN:0;
  assert(wr_iot_mcu_boot_pse_drain(&ad,live)==0&&calls==2&&delays==1);
 }
 for(mode=1;mode<=7;mode++){
  unsigned scenario=mode;fresh();mode=scenario;
  int ret=wr_iot_mcu_boot_pse_drain(&ad,1);
  assert(ret==((mode==4||mode==7)?0:1));
  if(mode==1||mode==2||mode==6)assert(calls==1);
  if(mode==3||mode==5)assert(calls==200&&delays==199);
  if(mode==4)assert(calls==4&&delays==3);
  if(mode==7)assert(calls==5&&delays==4);
 }
 fresh();hardware_cfg=0;mode=5;assert(wr_iot_mcu_boot_pse_drain(&ad,0)==1&&calls==1&&!delays);
 for(unsigned i=0;i<8;i++){
  fresh();unsigned live=1;
  switch(i){case 0:hardware_cfg=0;break;case 1:hardware_cfg=~0u;break;
   case 2:owned=0;break;case 3:atomic_context=1;break;case 4:irq_off=1;break;
   case 5:ad.flags=1;break;case 6:live=2;break;case 7:live=0;hardware_cfg=RX_DMA_BUSY;break;}
  assert(wr_iot_mcu_boot_pse_drain(&ad,live)==1&&!calls);ad.flags=0;
 }
 fresh();assert(wr_iot_mcu_boot_pse_drain(NULL,1)==1&&!calls);
 puts("PASS actual bounded PSE drain: both stages, immediate error, 200-attempt bound, consecutive-empty reset and context/DMA refusal; hardware observations injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-pse-drain-') as td:
    c = Path(td)/'check.c'
    c.write_text(fixture)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                    str(c), '-o', td+'/check'], check=True)
    subprocess.run([td+'/check'], check=True)
