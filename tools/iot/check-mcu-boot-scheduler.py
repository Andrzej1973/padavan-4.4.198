#!/usr/bin/env python3
"""Actual scheduler wrapper with injected SDK and MMIO observations."""
from pathlib import Path
import argparse
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path)
a=p.parse_args()
prefix=r'''
#include <assert.h>
#include <stdio.h>
typedef unsigned UINT32;typedef int INT32;
typedef struct {unsigned wr_iot_boot_active,wr_iot_boot_failed,wr_iot_boot_frozen,wr_iot_boot_hw_state,wr_iot_boot_hw_stage,bPCIclkOff,flags;struct {unsigned Stage;} MCUCtrl;struct {int dma_mode;} fpga_ctl;} RTMP_ADAPTER;
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
#define fRTMP_ADAPTER_RESET_IN_PROGRESS 2u
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 4u
#define fRTMP_ADAPTER_SUSPEND 8u
#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define TRUE 1
#define FW_RUN_TIME 3
#define TOP_MISC2 1
#define MCU_PCIE_REMAP_2 2
#define MT_SCH_REG_4 3
#define DMA_SCH_LMAC 0
#define MT7603 0
#define MT7603E1 0
#define IS_MT7603(ad) ((void)(ad),1)
#define in_atomic() 0
#define irqs_disabled() 0
static unsigned fault,reads,calls,rev,writes;
static int wr_iot_mcu_boot_owned(RTMP_ADAPTER *ad){assert(ad);return fault!=11&&!(fault==12&&calls);}
#define MTK_REV_GTE(ad,x,y) ((void)(ad),(void)(x),(void)(y),rev)
static unsigned observe(unsigned reg){reads++;if(reg==1)return fault==1?~0u:(fault==7&&calls?1:2);if(reg==2)return fault==2?~0u:(fault==4&&calls?0x22:0x11);return fault==5?~0u:rev?0x40:0;}
#define RTMP_IO_READ32(ad,r,out) ((void)(ad),*(out)=observe(r))
#define RTMP_IO_WRITE32(ad,r,v) do{assert(ad&&(r)==MCU_PCIE_REMAP_2&&(v)==0x11);writes++;}while(0)
static int AsicDMASchedulerInit(RTMP_ADAPTER *ad,int mode){assert(ad&&mode==0);calls++;if(fault==8)ad->wr_iot_boot_failed=1;if(fault==14)ad->flags=1;if(fault==15)ad->bPCIclkOff=1;return fault==3?0:1;}
'''
tail=r'''
int main(void){for(rev=0;rev<2;rev++)for(fault=0;fault<16;fault++){
 RTMP_ADAPTER a={0};a.wr_iot_boot_active=1;a.wr_iot_boot_hw_state=2;a.wr_iot_boot_hw_stage=6;a.MCUCtrl.Stage=3;reads=calls=writes=0;
 if(fault==6)a.wr_iot_boot_frozen=1;
 if(fault==9)a.fpga_ctl.dma_mode=1;
 if(fault==10)a.bPCIclkOff=1;
 if(fault==13)a.flags=2;
 unsigned bad=fault!=0;
#ifndef CONFIG_FPGA_MODE
 if(fault==9)bad=0;
#endif
 assert(wr_iot_mcu_boot_scheduler_check(&a)==(bad?1:0));
 assert(writes==(fault==4));
#ifdef CONFIG_FPGA_MODE
 if(fault==9)assert(!reads&&!calls);
#endif
 if(fault==6)assert(!reads&&!calls);
 if(fault==10)assert(!reads&&!calls);
 if(fault==11)assert(!reads&&!calls);
 if(fault==13)assert(!reads&&!calls);
 if(fault==1||fault==2)assert(!calls);
}puts("PASS scheduler wrapper: both revisions, invalid RUN/remap/SDK/mode and frozen refusal; SDK/MMIO injected");}
'''
with tempfile.TemporaryDirectory(prefix='wr-scheduler-') as td:
 c=Path(td)/'test.c';body=(a.candidate/'include/wr-iot-mcu-boot-scheduler.inc').read_text()
 c.write_text(prefix+body+tail)
 for flags in ([],['-DCONFIG_FPGA_MODE']):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',td+'/test'],check=True)
  subprocess.run([td+'/test'],check=True)
 # Keep the SDK call but deliberately accept its failure: fault3 must detect it.
 mutated=body.replace('if(result!=TRUE)return NDIS_STATUS_FAILURE;', '(void)result;',1)
 assert mutated!=body
 c.write_text(prefix+mutated+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',str(c),'-o',td+'/mutant'],check=True)
 result=subprocess.run([td+'/mutant'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 assert result.returncode!=0,'SDK-result mutation survived'
 print('PASS executed mutation: accepting SDK failure is rejected')
