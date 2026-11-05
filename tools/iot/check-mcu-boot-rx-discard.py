#!/usr/bin/env python3
"""Run actual bounded RX discard with SDK descriptor layout; DMA/IRQ injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
sdk=(a.candidate/'include/mac/mac_mt/mt_mac_pci.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tstruct GNU_PACKED _RXD_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */');layout=sdk[start:end]
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "tasklet-schedule-owner.h"
typedef uint32_t UINT32;typedef unsigned long ULONG;typedef unsigned char UCHAR;typedef int INT;
#define GNU_PACKED __attribute__((packed))
@@LAYOUT@@
#define RXD_SIZE 16
#define RX_RING_SIZE 4
#define RX_BUFFER_AGGRESIZE 2048
#define NUM_OF_RX_RING 2
#define MT_RX_RING_CIDX 200
#define MT_RX_RING_DIDX 100
#define MT_RINGREG_DIFF 16
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define HIF_MT 1
#define TOP_MISC2 1
#define MT_INT_MASK_CSR 2
#define ARB_SCR 3
#define MT_ARB_SCR_TXDIS 0x100u
#define MT_ARB_SCR_RXDIS 0x200u
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
struct buffer {void *AllocVa;unsigned AllocSize;UINT32 AllocPa;};
typedef struct {void *AllocVa;unsigned AllocSize;void *pNdisPacket;struct buffer DmaBuf;} RTMP_DMACB;
typedef struct {RTMP_DMACB Cell[RX_RING_SIZE];UINT32 RxSwReadIdx,RxCpuIdx,RxDmaIdx,hw_didx_addr,hw_cidx_addr;} RTMP_RX_RING;
typedef struct {struct {int hif_type;} chipCap;unsigned flags;int wr_iot_nettask_lock;unsigned wr_iot_nettask_joined,wr_iot_nettask_data_joined,wr_iot_boot_mcu_only,wr_iot_nettask_initializing,wr_iot_nettask_data_joining;struct wr_iot_tasklet_schedule_owner wr_iot_nettask_owner,wr_iot_nettask_data_owner;RTMP_RX_RING RxRing[2];struct buffer RxDescRing[2];int RxRingLock[2];} RTMP_ADAPTER;
static unsigned held,context,mode,writes,read_barriers,write_barriers;
static UINT32 dma[2],cpu_hw[2];static RTMP_ADAPTER *current;
union descriptor {RXD_STRUC d;UINT32 word[4];};static union descriptor descriptors[2][4];
#define in_atomic() 0
#define irqs_disabled() 0
#define IS_MT7603(ad) ((void)(ad),1)
#define RTMP_TEST_FLAG(ad,flag) ((ad)->flags&(flag))
#define RTMP_GetPhysicalAddressLow(pa) ((UINT32)(pa))
#define le2cpu32(v) (v)
#define cpu2le32(v) (v)
#define RTMP_INT_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define RTMP_SEM_LOCK(l) do{(void)(l);assert(!held);held=1;}while(0)
#define RTMP_SEM_UNLOCK(l) do{(void)(l);assert(held);held=0;}while(0)
#define rmb() (read_barriers++)
#define wmb() (write_barriers++)
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(ad==current&&!held);return context;}
static UINT32 read_register(unsigned reg){
 if(reg==TOP_MISC2)return mode==1?2:1;
 if(reg==MT_INT_MASK_CSR)return mode==2?1:0;
 if(reg==ARB_SCR)return mode==3?0:0x300;
 assert(held);if(reg==200||reg==216)return cpu_hw[(reg-200)/16];
 assert(reg==100||reg==116);return mode==4?~0u:dma[(reg-100)/16];
}
static void write_register(unsigned reg,unsigned index){
 assert(held&&(reg==200||reg==216)&&index<4);unsigned ring=(reg-200)/16;
 union descriptor *d=&descriptors[ring][index];
 assert(!d->d.DDONE&&d->d.SDL0==2048&&!d->d.SDL1&&!d->d.LS0&&!d->d.LS1);
 assert(d->word[0]==0x1000+ring*0x100+index*0x10&&d->word[2]==0xcafe&&d->word[3]==0xbeef);
 assert(write_barriers==2*(writes+1)&&read_barriers==writes+1);writes++;
 if(mode!=7)cpu_hw[ring]=index;
 if(mode==5)context=0;
 if(mode==6)d->d.DDONE=1; /* Device continues producing; batch must stop. */
}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=read_register(reg))
#define RTMP_IO_WRITE32(ad,reg,value) ((void)(ad),write_register(reg,value))
'''.replace('@@LAYOUT@@',layout)+(a.candidate/'include/wr-iot-mcu-boot-rx-discard.inc').read_text()+r'''
static void fresh(RTMP_ADAPTER *ad,unsigned first,unsigned count){
 memset(ad,0,sizeof(*ad));memset(descriptors,0,sizeof(descriptors));current=ad;
 held=writes=read_barriers=write_barriers=mode=0;context=1;ad->chipCap.hif_type=1;
 ad->wr_iot_nettask_joined=ad->wr_iot_nettask_data_joined=1;
 wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_owner);wr_iot_tasklet_schedule_init(&ad->wr_iot_nettask_data_owner);
 for(unsigned ring=0;ring<2;ring++){
  RTMP_RX_RING *r=&ad->RxRing[ring];r->RxSwReadIdx=first;r->RxCpuIdx=(first+3)%4;r->hw_didx_addr=100+16*ring;r->hw_cidx_addr=200+16*ring;cpu_hw[ring]=r->RxCpuIdx;
  dma[ring]=(first+count)%4;ad->RxDescRing[ring].AllocVa=descriptors[ring];ad->RxDescRing[ring].AllocSize=sizeof(descriptors[ring]);
  for(unsigned i=0;i<4;i++){
   RTMP_DMACB *cell=&r->Cell[i];cell->AllocVa=&descriptors[ring][i];cell->AllocSize=16;
   cell->pNdisPacket=(void *)1;cell->DmaBuf.AllocVa=(void *)2;cell->DmaBuf.AllocSize=2048;cell->DmaBuf.AllocPa=0x1000+ring*0x100+i*0x10;
   descriptors[ring][i].word[0]=cell->DmaBuf.AllocPa;descriptors[ring][i].word[2]=0xcafe;descriptors[ring][i].word[3]=0xbeef;
  }
  for(unsigned i=0;i<count;i++){RXD_STRUC *d=&descriptors[ring][(first+i)%4].d;d->DDONE=d->LS0=d->LS1=1;d->SDL0=1;d->SDL1=7;}
 }
}
int main(void){
 RTMP_ADAPTER ad;unsigned empty;
 for(unsigned first=0;first<4;first++)for(unsigned count=0;count<4;count++){
  fresh(&ad,first,count);assert(!wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)&&empty&&writes==2*count&&!held);
  assert(ad.RxRing[0].RxSwReadIdx==dma[0]&&ad.RxRing[1].RxSwReadIdx==dma[1]);
 }
 for(unsigned fault=1;fault<=4;fault++){
  fresh(&ad,0,1);mode=fault;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&!empty&&!writes&&!held);
 }
 fresh(&ad,0,0);dma[0]=1;assert(!wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)&&!empty&&!writes); /* Index ahead, DDONE not yet visible. */
 fresh(&ad,0,1);ad.RxRing[1].Cell[3].pNdisPacket=NULL;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&!writes);
 fresh(&ad,0,1);ad.RxRing[0].RxSwReadIdx=4;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&!writes);
 fresh(&ad,0,1);descriptors[0][0].word[0]++;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&!writes);
 fresh(&ad,0,1);mode=5;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&writes==1&&!empty&&!held);
 fresh(&ad,0,0);mode=6;for(unsigned r=0;r<2;r++)for(unsigned i=0;i<4;i++)descriptors[r][i].d.DDONE=1;
 assert(!wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)&&!empty&&writes==8&&!held);
 fresh(&ad,0,1);mode=7;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&writes==1&&!empty&&!held);
 fresh(&ad,0,1);ad.RxRing[0].hw_cidx_addr++;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&!writes);
 fresh(&ad,0,1);cpu_hw[0]=0;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&!writes&&!held);
 fresh(&ad,0,1);ad.wr_iot_nettask_joined=0;assert(wr_iot_mcu_boot_rx_discard_batch(&ad,&empty)==1&&!writes);
 puts("PASS actual raw RX discard: SDK descriptor format, reduced4-entry geometry/all wraps, both rings, index/DDONE race, invalid mappings, context loss and bounded continuous producer; no payload/callback/alloc/free, DMA injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-rx-discard-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
