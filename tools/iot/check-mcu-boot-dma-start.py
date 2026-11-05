#!/usr/bin/env python3
"""Actual DMA start/stop and idle poll with SDK register layout, injected MMIO."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
sdk=(a.candidate/'include/iface/rtmp_reg_pcirbs.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tunion _WPDMA_GLO_CFG_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef int INT32;typedef int BOOLEAN;typedef uint32_t UINT32;
@@LAYOUT@@
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define MT_INT_MASK_CSR 1
#define ARB_SCR 2
#define MT_WPDMA_GLO_CFG 3
#define MT_ARB_SCR_TXDIS 1u
#define MT_ARB_SCR_RXDIS 2u
#define TX_DMA_EN 1u
#define RX_DMA_EN 4u
#define TX_DMA_BUSY 2u
#define RX_DMA_BUSY 8u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
typedef struct {struct {unsigned WPDMABurstSIZE;} chipCap;unsigned flags,wr_iot_boot_dma_state,wr_iot_boot_dma_saved_off,wr_iot_boot_dma_saved_valid,wr_iot_boot_dma_stop_verified;} RTMP_ADAPTER;
static unsigned fault,cfg,writes,queries,stop_phase,delays,mask_writes;
#define in_atomic() 0
#define irqs_disabled() 0
#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))
static int wr_iot_mcu_boot_dma_owned(RTMP_ADAPTER *ad){assert(ad&&ad->wr_iot_boot_dma_state==1);queries++;return !(fault==7&&queries==2);}
static unsigned rd(unsigned reg){
 if(reg==1)return fault==9||fault==6&&writes&&!stop_phase||fault==12&&stop_phase?1:0;
 if(reg==2)return fault==10||fault==5&&writes?0:3;
 assert(reg==3);
 if(!writes&&fault==1)return ~0u;
 if(!writes&&fault==2)return cfg|TX_DMA_EN;
 if(stop_phase)return fault==11?cfg|TX_DMA_EN:cfg;
 if(writes&&fault==3)return cfg^RX_DMA_EN;
 if(writes&&fault==4)return cfg|RX_DMA_BUSY;
 return cfg;
}
static void wr(unsigned reg,unsigned val){
 if(reg==1){assert(!val);mask_writes++;return;}
 assert(reg==3);writes++;cfg=val;
}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=rd(reg))
#define RTMP_IO_WRITE32(ad,reg,val) ((void)(ad),wr(reg,val))
#define RTMP_ASIC_INTERRUPT_DISABLE(ad) RTMP_IO_WRITE32(ad,1,0)
#define RtmpusecDelay(n) do{assert((n)==1000);delays++;}while(0)
'''.replace('@@LAYOUT@@',sdk[start:end])+(a.candidate/'include/wr-iot-mcu-dma-disabled-idle.inc').read_text()+'\n'+(a.candidate/'include/wr-iot-mcu-boot-dma-start.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=12;fault++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_dma_state=1;ad.chipCap.WPDMABurstSIZE=fault==8?4:3;
  cfg=0x52000850;writes=queries=stop_phase=delays=mask_writes=0;
  unsigned success=fault==0||fault==4||fault==11||fault==12;
  assert(wr_iot_mcu_boot_dma_start_hw(&ad)==(success?0:1));
  if(writes){assert(writes==1&&ad.wr_iot_boot_dma_saved_valid&&ad.wr_iot_boot_dma_saved_off==0x52000850);
   WPDMA_GLO_CFG_STRUC expected;expected.word=0x52000850;expected.field.EnableTxDMA=expected.field.EnableRxDMA=expected.field.EnTXWriteBackDDONE=1;expected.field.WPDMABurstSIZE=3;
   assert(cfg==expected.word);stop_phase=1;
   assert(wr_iot_mcu_boot_dma_stop_hw(&ad)==(fault==11||fault==12?1:0));
   assert(cfg==0x52000850&&writes==2&&mask_writes==1);
   assert(ad.wr_iot_boot_dma_stop_verified==(unsigned)(fault!=11&&fault!=12));
   assert(delays<=200);
  }else {assert(!ad.wr_iot_boot_dma_saved_valid&&!mask_writes);
   assert(wr_iot_mcu_boot_dma_stop_hw(&ad)==1&&!writes);}
 }
 puts("PASS actual SDK DMA enable/readback and bounded stop: config preservation, legitimate busy, partial/bus/MAC/IRQ/context refusal and unknown-stop retention; no MAC/IRQ enable, MMIO injected");
}
'''
fixture=fixture.replace('fault==9||fault==6&&writes&&!stop_phase||fault==12&&stop_phase',
                        'fault==9||(fault==6&&writes&&!stop_phase)||(fault==12&&stop_phase)')
fixture=fixture.replace('fault==10||fault==5&&writes','fault==10||(fault==5&&writes)')
with tempfile.TemporaryDirectory(prefix='wr-mcu-dma-start-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
