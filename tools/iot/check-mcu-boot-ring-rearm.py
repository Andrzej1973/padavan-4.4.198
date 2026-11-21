#!/usr/bin/env python3
"""Actual narrow ring programming with SDK descriptors/reset layout and injected MMIO."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
sdk=(a.candidate/'include/mac/mac_mt/mt_mac_pci.h').read_text()
def layout(name):
 start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tstruct GNU_PACKED _'+name+'_STRUC'))
 end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
 return sdk[start:end]
reg=(a.candidate/'include/iface/rtmp_reg_pcirbs.h').read_text()
start=reg.rfind('#ifdef RT_BIG_ENDIAN',0,reg.index('typedef union _WPDMA_RST_IDX_STRUC'))
end=reg.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include <stdio.h>
typedef int INT;typedef uint32_t UINT32;typedef unsigned char UCHAR;typedef unsigned long ULONG;
#define GNU_PACKED __attribute__((packed))
@@LAYOUT@@
#define TXD_SIZE 16
#define RXD_SIZE 16
#define RX_RING_SIZE 4
#define MGMT_RING_SIZE 4
#define NUM_OF_RX_RING 2
#define RX_BUFFER_AGGRESIZE 2048
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define MT_TX_RING_BASE 100
#define MT_RX_RING_BASE 300
#define MT_RINGREG_DIFF 16
#define WPDMA_RST_PTR 500
typedef struct {void *AllocVa;unsigned AllocSize;uint64_t AllocPa;} RTMP_DMABUF;
typedef struct {void *AllocVa;unsigned AllocSize;uint64_t AllocPa;void *pNdisPacket,*pNextNdisPacket;RTMP_DMABUF DmaBuf;} RTMP_DMACB;
typedef struct {RTMP_DMACB Cell[4];unsigned TxSwFreeIdx,TxCpuIdx,TxDmaIdx,hw_desc_base,hw_cnt_addr,hw_cidx_addr,hw_didx_addr;} RTMP_CTRL_RING;
typedef struct {RTMP_DMACB Cell[4];unsigned RxSwReadIdx,RxCpuIdx,RxDmaIdx,hw_desc_base,hw_cnt_addr,hw_cidx_addr,hw_didx_addr;} RTMP_RX_RING;
typedef struct {RTMP_CTRL_RING CtrlRing;RTMP_RX_RING RxRing[2];RTMP_DMABUF CtrlDescRing,RxDescRing[2];} RTMP_ADAPTER;
static unsigned fault,guards,writes,reads,barriers,regs[512];static uint32_t descs[3][4][4];
#define in_atomic() 0
#define irqs_disabled() 0
#define NdisZeroMemory(p,n) memset(p,0,n)
#define RTMP_GetPhysicalAddressHigh(p) ((p)>>32)
#define RTMP_GetPhysicalAddressLow(p) ((UINT32)(p))
#define le2cpu32(v) (v)
#define wmb() (barriers++)
static int wr_iot_mcu_boot_pse_empty(RTMP_ADAPTER *ad){assert(ad);guards++;return !(fault==1&&guards==1)&&!(fault==2&&guards==2)&&!(fault==3&&guards==3);}
static void wr(unsigned reg,unsigned value){
 writes++;
 if(reg==500){assert(value==0x30020);for(unsigned i=0;i<3;i++)regs[(i?300+16*(i-1):180)+12]=0;return;}
 unsigned which=reg>=300?(reg-300)/16:0;unsigned base=reg>=300?300+which*16:180;
 assert(which<2&&(reg==base||reg==base+4||reg==base+8));regs[reg]=value;
}
static unsigned rd(unsigned reg){assert(reg<512);reads++;return fault>=4&&fault<=15&&reads==fault-3?~0u:regs[reg];}
#define RTMP_IO_WRITE32(ad,reg,value) ((void)(ad),wr(reg,value))
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=rd(reg))
'''.replace('@@LAYOUT@@',layout('TXD')+'\n'+layout('RXD')+'\n'+reg[start:end])+(a.candidate/'include/wr-iot-mcu-boot-ring-rearm.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=20;fault++){
  RTMP_ADAPTER ad={0};guards=writes=reads=barriers=0;memset(descs,0,sizeof(descs));
  for(unsigned r=0;r<512;r++)regs[r]=0x12345678;
  ad.CtrlRing.TxCpuIdx=ad.CtrlRing.TxSwFreeIdx=ad.CtrlRing.TxDmaIdx=3;
  for(unsigned i=0;i<3;i++){
   RTMP_DMABUF *buf=i?&ad.RxDescRing[i-1]:&ad.CtrlDescRing;
   *buf=(RTMP_DMABUF){descs[i],sizeof(descs[i]),0x1000+0x100*i};
   if(i)ad.RxRing[i-1].RxSwReadIdx=ad.RxRing[i-1].RxDmaIdx=ad.RxRing[i-1].RxCpuIdx=2;
   for(unsigned j=0;j<4;j++){
    RTMP_DMACB *c=i?&ad.RxRing[i-1].Cell[j]:&ad.CtrlRing.Cell[j];
    c->AllocVa=descs[i][j];c->AllocSize=16;c->AllocPa=buf->AllocPa+16*j;
    if(!i)((TXD_STRUC *)c->AllocVa)->DMADONE=1;
    else {c->pNdisPacket=(void *)1;c->DmaBuf=(RTMP_DMABUF){(void *)2,2048,0x4000+i*0x100+j*0x10};RXD_STRUC *rx=c->AllocVa;rx->SDP0=(UINT32)c->DmaBuf.AllocPa;rx->SDL0=2048;}
   }
  }
  switch(fault){case 16:ad.CtrlRing.Cell[3].pNdisPacket=(void *)1;break;
   case 17:((RXD_STRUC *)ad.RxRing[1].Cell[3].AllocVa)->DDONE=1;break;
   case 18:ad.RxRing[1].Cell[3].AllocPa++;break;
   case 19:ad.RxDescRing[1].AllocPa|=1;break;
   case 20:ad.CtrlDescRing.AllocSize=1;break;}
  assert(wr_iot_mcu_boot_ring_rearm(&ad)==(fault?1:0));
  if(!fault){assert(writes==10&&reads==12&&barriers==1&&!ad.CtrlRing.TxCpuIdx);for(unsigned i=0;i<2;i++)assert(!ad.RxRing[i].RxSwReadIdx&&!ad.RxRing[i].RxDmaIdx&&ad.RxRing[i].RxCpuIdx==3);}
  else {assert(ad.CtrlRing.TxCpuIdx==3);for(unsigned i=0;i<2;i++)assert(ad.RxRing[i].RxSwReadIdx==2);}
  if(fault==1||fault==2||fault>=16)assert(!writes);
  for(unsigned r=0;r<512;r++){
   unsigned touched=0;for(unsigned i=0;i<3;i++){unsigned b=i?300+16*(i-1):180;if(r>=b&&r<=b+12&&(r-b)%4==0)touched=1;}
   if(!touched)assert(regs[r]==0x12345678);
  }
 }
 puts("PASS actual narrow ring rearm: SDK reset mask CTRL5/RX0/RX1, descriptor inventory, all12 readback failures, delayed software publication, untouched other registers; MMIO injected, no epoch/runtime proof");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-ring-rearm-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
