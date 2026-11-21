#!/usr/bin/env python3
"""Actual read-only seven-ring gate with SDK TXD, injected rings/MMIO."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
sdk=(a.candidate/'include/mac/mac_mt/mt_mac_pci.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tstruct GNU_PACKED _TXD_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "tasklet-schedule-owner.h"
typedef int INT;typedef uint32_t UINT32;typedef unsigned long ULONG;typedef unsigned char UCHAR;
#define GNU_PACKED __attribute__((packed))
@@LAYOUT@@
#define NUM_OF_TX_RING 4
#define TX_RING_SIZE 2
#define MGMT_RING_SIZE 2
#define BCN_RING_SIZE 2
#define TXD_SIZE 16
#define QID_AC_BE 0
#define QID_AC_BK 1
#define QID_BMC 8
#define MT_TX_RING_BCN_IDX 7
#define MT_RINGREG_DIFF 16
#define MT_TX_RING_BASE 100
#define MT_INT_MASK_CSR 1
#define MT_WPDMA_GLO_CFG 2
#define TX_DMA_EN 1u
#define RX_DMA_EN 4u
#define TX_DMA_BUSY 2u
#define RX_DMA_BUSY 8u
#define NDIS_STATUS_FAILURE 1
#define NDIS_STATUS_SUCCESS 0
typedef struct {void *AllocVa;unsigned AllocSize;uint64_t AllocPa;} RTMP_DMABUF;
typedef struct {void *AllocVa;unsigned AllocSize;uint64_t AllocPa;void *pNdisPacket,*pNextNdisPacket;} RTMP_DMACB;
typedef struct {RTMP_DMACB Cell[2];unsigned TxSwFreeIdx,TxCpuIdx,hw_desc_base,hw_cnt_addr,hw_cidx_addr,hw_didx_addr;} RING;
typedef struct {RING TxRing[4],MgmtRing,TxBmcRing,BcnRing;RTMP_DMABUF TxDescRing[4],MgmtDescRing,TxBmcDescRing,BcnDescRing;int wr_iot_nettask_lock;unsigned wr_iot_nettask_data_joined,wr_iot_nettask_data_joining;struct wr_iot_tasklet_schedule_owner wr_iot_nettask_data_owner;} RTMP_ADAPTER;
static unsigned held,context,regs[512],reads;static UINT32 descriptors[7][2][4];
#define in_atomic() 0
#define irqs_disabled() 0
#define RTMP_GetPhysicalAddressHigh(p) ((p)>>32)
#define RTMP_GetPhysicalAddressLow(p) ((UINT32)(p))
#define RTMP_INT_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
static int wr_iot_mcu_boot_frozen_owned(RTMP_ADAPTER *ad){assert(ad&&!held);return context;}
static unsigned rd(unsigned reg){assert(!held&&reg<512);reads++;return regs[reg];}
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=rd(reg))
'''.replace('@@LAYOUT@@',sdk[start:end])+(a.candidate/'include/wr-iot-mcu-boot-other-tx-idle.inc').read_text()+r'''
int main(void){
 for(unsigned which=0;which<7;which++)for(unsigned fault=0;fault<=11;fault++){
  RTMP_ADAPTER ad={0};held=reads=0;context=1;memset(regs,0,sizeof(regs));memset(descriptors,0,sizeof(descriptors));
  ad.wr_iot_nettask_data_joined=1;wr_iot_tasklet_schedule_init(&ad.wr_iot_nettask_data_owner);ad.wr_iot_nettask_data_owner.blocked=1;
  RING *rings[7]={&ad.TxRing[0],&ad.TxRing[1],&ad.TxRing[2],&ad.TxRing[3],&ad.MgmtRing,&ad.TxBmcRing,&ad.BcnRing};
  RTMP_DMABUF *buffers[7]={&ad.TxDescRing[0],&ad.TxDescRing[1],&ad.TxDescRing[2],&ad.TxDescRing[3],&ad.MgmtDescRing,&ad.TxBmcDescRing,&ad.BcnDescRing};
  for(unsigned i=0;i<7;i++){
   unsigned offset=(unsigned[]){16,0,32,48,64,128,112}[i];RING *r=rings[i];RTMP_DMABUF *b=buffers[i];
   *b=(RTMP_DMABUF){descriptors[i],sizeof(descriptors[i]),0x1000+i*0x100};
   r->TxCpuIdx=r->TxSwFreeIdx=i%2;r->hw_desc_base=100+offset;r->hw_cnt_addr=r->hw_desc_base+4;r->hw_cidx_addr=r->hw_desc_base+8;r->hw_didx_addr=r->hw_desc_base+12;
   regs[r->hw_desc_base]=(unsigned)b->AllocPa;regs[r->hw_cnt_addr]=2;regs[r->hw_cidx_addr]=regs[r->hw_didx_addr]=r->TxCpuIdx;
   for(unsigned j=0;j<2;j++){r->Cell[j]=(RTMP_DMACB){descriptors[i][j],16,b->AllocPa+j*16,NULL,NULL};((TXD_STRUC *)descriptors[i][j])->DMADONE=1;}
  }
  RING *bad=rings[which];RTMP_DMABUF *buf=buffers[which];
  switch(fault){case 1:bad->Cell[1].pNdisPacket=(void *)1;break;case 2:bad->Cell[1].pNextNdisPacket=(void *)1;break;
   case 3:((TXD_STRUC *)bad->Cell[1].AllocVa)->DMADONE=0;break;case 4:regs[bad->hw_didx_addr]^=1;break;
   case 5:regs[bad->hw_desc_base]=~0u;break;case 6:regs[bad->hw_cnt_addr]=3;break;
   case 7:bad->Cell[1].AllocPa++;break;case 8:buf->AllocSize=1;break;
   case 9:regs[2]=TX_DMA_EN;break;case 10:ad.wr_iot_nettask_data_owner.blocked=0;break;case 11:regs[1]=1;break;}
  RING before[7];for(unsigned i=0;i<7;i++)before[i]=*rings[i];unsigned before_regs[512];memcpy(before_regs,regs,sizeof(regs));
  assert(wr_iot_mcu_boot_other_tx_idle(&ad)==(fault?1:0)&&!held);
  assert(!memcmp(before_regs,regs,sizeof(regs)));for(unsigned i=0;i<7;i++)assert(!memcmp(&before[i],rings[i],sizeof(RING)));
 }
 puts("PASS actual other-TX idle gate: all7 rings, pending packets/descriptors, DMA indices/base/count/address/storage, data fence, DMA/IRQ refusal; read-only, reduced geometry, MMIO injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-other-tx-idle-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
