#!/usr/bin/env python3
"""Exercise actual composed ROM actor; hardware, joins and drain operations injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path)
a=p.parse_args()
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef int INT32;typedef uint32_t UINT32;
#define FALSE 0
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_SUCCESS 0
#define HIF_MT 1
#define MCU_INIT 0
#define TOP_MISC2 1
#define MT_INT_MASK_CSR 2
#define ARB_SCR 3
#define ASIC_MAC_TXRX 4
#define MT_ARB_SCR_TXDIS 1u
#define MT_ARB_SCR_RXDIS 2u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
struct pci {int irq;};struct cookie {struct pci *pci_dev;};typedef struct cookie *POS_COOKIE;
struct MCU_CTRL {unsigned flags;int txq,ackq,rxq,kickq,tx_doneq,rx_doneq;};
typedef struct adapter {void *OS_Cookie;struct MCU_CTRL MCUCtrl;struct {int hif_type;} chipCap;unsigned wr_iot_boot_mcu_only,flags;struct {void (*MCUCtrlExit)(struct adapter *);} chipOps;} RTMP_ADAPTER;
#define in_atomic() 0
#define irqs_disabled() 0
#define IS_MT7603(ad) ((void)(ad),1)
#define OS_TEST_BIT(bit,p) ((void)(bit),*(p)&1)
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
static unsigned fault,stage,masked,synced,frozen,context,exited,reads;
static unsigned rd(unsigned reg){
 reads++;
 if(reg==TOP_MISC2)return fault==1?2:1;
 if(reg==ARB_SCR)return fault==4?0:3;
 assert(reg==MT_INT_MASK_CSR);return fault==5||(fault==8&&masked==2)?1:0;
}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=rd(reg))
static int wr_iot_mcu_boot_owned(RTMP_ADAPTER *ad){assert(ad);return context;}
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(ad);return frozen&&context;}
static int wr_iot_mcu_boot_freeze(RTMP_ADAPTER *ad){assert(ad&&stage==0);frozen=1;stage=1;return fault==2?1:0;}
static int AsicSetMacTxRx(RTMP_ADAPTER *ad,int which,int enabled){assert(ad&&stage==1&&which==4&&!enabled);stage=2;return fault!=3;}
static void mask_irq(RTMP_ADAPTER *ad){assert(ad&&(stage==2||stage==4));masked++;stage=3;}
#define RTMP_ASIC_INTERRUPT_DISABLE mask_irq
static void synchronize_irq(int irq){assert(irq==7&&(stage==3||stage==6));synced++;if(fault==6)context=0;}
static int RtmpNetTaskExit(RTMP_ADAPTER *ad){assert(stage==3&&synced==1);stage=4;if(fault==7)return 1;ad->wr_iot_boot_mcu_only=0;return 0;}
static int wr_iot_mcu_boot_pse_drain(RTMP_ADAPTER *ad,unsigned live){
 assert(ad&&!ad->wr_iot_boot_mcu_only);
 if(live){assert(stage==3&&masked==2&&synced==2);stage=5;return fault==9?1:0;}
 assert(stage==6&&synced==3);stage=7;return fault==11?1:0;
}
static void AndesMTPciFwExit(RTMP_ADAPTER *ad){assert(ad&&stage==5);stage=6;}
static int wr_iot_mcu_dma_disabled_idle(RTMP_ADAPTER *ad){assert(ad&&(stage==6||stage==8));return fault!=10;}
static unsigned AndesQueueLen(struct MCU_CTRL *ctl,int *q){assert(stage==7);return fault==12&&q==&ctl->ackq?1:0;}
static void controller_exit(RTMP_ADAPTER *ad){assert(stage==7);stage=8;exited++;if(fault!=13)ad->MCUCtrl.flags=0;}
#define AndesCtrlExit controller_exit
#define MCU_CTRL_EXIT controller_exit
static int wr_iot_mcu_boot_pse_empty(RTMP_ADAPTER *ad){assert(ad&&stage==8);return fault!=14;}
'''+(a.candidate/'include/wr-iot-mcu-boot-rom-quiesce.inc').read_text()+r'''
int main(void){
 struct pci pci={7};struct cookie cookie={&pci};
 for(fault=0;fault<=14;fault++){
  RTMP_ADAPTER ad={0};ad.OS_Cookie=&cookie;ad.chipCap.hif_type=1;
  ad.wr_iot_boot_mcu_only=1;ad.MCUCtrl.flags=1;ad.chipOps.MCUCtrlExit=controller_exit;
  stage=masked=synced=frozen=exited=reads=0;context=1;
  assert(wr_iot_mcu_boot_rom_quiesce(&ad)==(fault?1:0));
  assert(reads<12);
  if(!fault)assert(stage==8&&masked==2&&synced==3&&exited==1&&!ad.MCUCtrl.flags);
  if(fault&&fault<13)assert(!exited);
  if(fault>1)assert(frozen);
 }
 puts("PASS actual composed ROM actor: MAC stop, mask/sync/join/remask, live drain before DMA stop, final discard/controller exit and PSE postcheck; 14 injected failures, no ring epoch claim");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-drain-order-') as td:
    c=Path(td)/'check.c';c.write_text(fixture)
    subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
    subprocess.run([td+'/check'],check=True)
