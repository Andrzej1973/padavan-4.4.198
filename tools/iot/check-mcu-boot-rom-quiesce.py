#!/usr/bin/env python3
"""Execute actual ROM quiesce + DMA readback helpers with injected hardware/joins."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
if 'wr_iot_mcu_boot_pse_drain(ad,1)' in (a.candidate/'include/wr-iot-mcu-boot-rom-quiesce.inc').read_text():
 subprocess.run(['python3',str(Path(__file__).with_name('check-mcu-boot-drain-order.py')),str(a.candidate)],check=True)
 raise SystemExit(0)
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef int INT32;typedef int BOOLEAN;typedef uint32_t UINT32;
#define TRUE 1
#define FALSE 0
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define HIF_MT 1
#define MCU_INIT 0
#define TOP_MISC2 1
#define MT_INT_MASK_CSR 2
#define MT_WPDMA_GLO_CFG 3
#define TX_DMA_EN 1u
#define RX_DMA_EN 4u
#define TX_DMA_BUSY 2u
#define RX_DMA_BUSY 8u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
struct pci {int irq;};struct cookie {struct pci *pci_dev;};typedef struct cookie *POS_COOKIE;
struct MCU_CTRL {unsigned flags;int txq,ackq,rxq,kickq,tx_doneq,rx_doneq;};
typedef struct adapter {void *OS_Cookie;struct MCU_CTRL MCUCtrl;struct {int hif_type;} chipCap;unsigned wr_iot_boot_mcu_only,flags;struct {void (*MCUCtrlExit)(struct adapter *);} chipOps;} RTMP_ADAPTER;
#define in_atomic() 0
#define irqs_disabled() 0
#define IS_MT7603(ad) ((void)(ad),1)
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
static unsigned fault,stage,order,freeze_at,stop_at,sync_at,join_at,exit_at,rom_reads,dma_reads,mask_reads,delays,frozen,context;
static unsigned read_register(unsigned reg){
 if(reg==TOP_MISC2){rom_reads++;if(fault==1)return 0;if(fault==2)return ~0u;return fault==10&&rom_reads>1?2:1;}
 if(reg==MT_INT_MASK_CSR){mask_reads++;return fault==4||(fault==11&&stage==4)?1:0;}
 assert(reg==MT_WPDMA_GLO_CFG);dma_reads++;return fault==5||(fault==12&&stage==4)?TX_DMA_EN:0;
}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=read_register(reg))
#define RtmpusecDelay(n) ((void)(n),delays++)
static int wr_iot_mcu_boot_owned(RTMP_ADAPTER *ad){assert(ad);return fault!=15&&context;}
static int wr_iot_mcu_boot_freeze(RTMP_ADAPTER *ad){assert(ad&&stage==0);freeze_at=++order;frozen=1;return fault==3?1:0;}
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(ad);return frozen&&context;}
static void AndesMTPciFwExit(RTMP_ADAPTER *ad){assert(ad&&frozen&&stage==0);stage=1;stop_at=++order;}
static void synchronize_irq(int irq){assert(irq==7&&stage==1&&dma_reads>=2&&mask_reads);stage=2;sync_at=++order;if(fault==6)context=0;}
static int RtmpNetTaskExit(RTMP_ADAPTER *ad){assert(stage==2);join_at=++order;if(fault==7)return 1;ad->wr_iot_boot_mcu_only=0;stage=3;return 0;}
static unsigned AndesQueueLen(struct MCU_CTRL *ctl,int *q){assert(stage==3);return fault==8&&q==&ctl->ackq?1:0;}
static void controller_exit(RTMP_ADAPTER *ad){assert(stage==3&&!ad->wr_iot_boot_mcu_only);stage=4;exit_at=++order;if(fault!=9)ad->MCUCtrl.flags=0;if(fault==14)context=0;if(fault==13)ad->flags|=fRTMP_ADAPTER_NIC_NOT_EXIST;}
#define MCU_CTRL_EXIT controller_exit
#define AndesCtrlExit controller_exit
'''+(a.candidate/'include/wr-iot-mcu-dma-disabled-idle.inc').read_text()+'\n'+(a.candidate/'include/wr-iot-mcu-boot-rom-quiesce.inc').read_text()+r'''
int main(void){
 struct pci pci={7};struct cookie cookie={&pci};
 for(fault=0;fault<=16;fault++){
  RTMP_ADAPTER ad={0};ad.OS_Cookie=&cookie;ad.chipCap.hif_type=1;ad.wr_iot_boot_mcu_only=1;ad.MCUCtrl.flags=1;ad.chipOps.MCUCtrlExit=fault==16?NULL:controller_exit;
  stage=order=freeze_at=stop_at=sync_at=join_at=exit_at=rom_reads=dma_reads=mask_reads=delays=frozen=0;context=1;
  int ret=wr_iot_mcu_boot_rom_quiesce(&ad);
  assert(ret==(fault?1:0)&&dma_reads<=202);
  if(!fault){assert(freeze_at<stop_at&&stop_at<sync_at&&sync_at<join_at&&join_at<exit_at);assert(!ad.MCUCtrl.flags&&!ad.wr_iot_boot_mcu_only&&frozen);}
  if(fault==1||fault==2||fault==15||fault==16)assert(!freeze_at&&!stop_at&&!exit_at);
  if(fault==3)assert(frozen&&!stop_at&&!sync_at);
  if(fault==4||fault==5)assert(stop_at&&!sync_at&&!join_at&&!exit_at);
  if(fault==6||fault==7||fault==8)assert(join_at&&!exit_at&&frozen);
  if(fault>=9&&fault<=14)assert(exit_at&&frozen);
 }
 puts("PASS actual ROM quiesce/DMA readback: ROM-first ordering, construction fence, IRQ mask/sync, RX join, empty queues, controller exit, postchecks and failure retention; hardware/joins injected, no ring epoch proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-rom-quiesce-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
