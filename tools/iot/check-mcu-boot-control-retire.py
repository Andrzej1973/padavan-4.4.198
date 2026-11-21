#!/usr/bin/env python3
"""Actual control retirement with SDK descriptor, injected packet/DMA ownership."""
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
#include <string.h>
#include <stdio.h>
typedef int INT;typedef unsigned UINT;typedef uint32_t UINT32;typedef unsigned long ULONG;typedef unsigned char UCHAR;typedef void *PNDIS_PACKET;
#define GNU_PACKED __attribute__((packed))
@@LAYOUT@@
#define TXD_SIZE 16
#define MGMT_RING_SIZE 4
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define RTMP_PCI_DMA_TODEVICE 1
typedef struct {void *AllocVa;unsigned AllocSize;PNDIS_PACKET pNdisPacket,pNextNdisPacket;uint64_t PacketPa;} RTMP_DMACB;
typedef struct {RTMP_DMACB Cell[4];unsigned TxSwFreeIdx,TxCpuIdx,TxDmaIdx;} RTMP_CTRL_RING;
typedef struct {RTMP_CTRL_RING CtrlRing;struct {void *AllocVa;unsigned AllocSize;} CtrlDescRing;int CtrlRingLock;} RTMP_ADAPTER;
typedef int PACKET_INFO;
static unsigned fault,held,guards,unmaps,frees,barriers,live[4],mapped[4];static uint32_t descriptors[4][4];
#define in_atomic() 0
#define irqs_disabled() 0
#define RTMP_GetPhysicalAddressHigh(p) ((p)>>32)
#define RTMP_GetPhysicalAddressLow(p) ((UINT32)(p))
#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;assert(!held);held=1;}while(0)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define NdisZeroMemory(p,n) memset(p,0,n)
#define wmb() (barriers++)
static int wr_iot_mcu_boot_pse_empty(RTMP_ADAPTER *ad){assert(ad&&!held);guards++;return !(fault==1&&guards==1)&&!(fault==10&&guards==2);}
static void RTMP_QueryPacketInfo(void *packet,PACKET_INFO *info,UCHAR **data,UINT *length){assert(packet&&held);*info=0;*data=(UCHAR *)packet;*length=fault==7?33:32;}
static void unmap(RTMP_ADAPTER *ad,uint64_t pa,unsigned len,int direction){assert(ad&&held&&pa<4&&len==32&&direction==1&&mapped[pa]);mapped[pa]=0;unmaps++;}
#define PCI_UNMAP_SINGLE unmap
static void release(RTMP_ADAPTER *ad,void *packet,int status){unsigned i=(unsigned)(uintptr_t)packet-1;assert(ad&&held&&!status&&i<4&&live[i]&&!mapped[i]);live[i]=0;frees++;}
#define RELEASE_NDIS_PACKET release
'''.replace('@@LAYOUT@@',sdk[start:end])+(a.candidate/'include/wr-iot-mcu-boot-control-retire.inc').read_text()+r'''
int main(void){
 for(fault=0;fault<=11;fault++){
  RTMP_ADAPTER ad={0};held=guards=unmaps=frees=barriers=0;
  memset(descriptors,0,sizeof(descriptors));
  ad.CtrlDescRing.AllocVa=descriptors;ad.CtrlDescRing.AllocSize=sizeof(descriptors);
  ad.CtrlRing.TxCpuIdx=3;ad.CtrlRing.TxSwFreeIdx=1;ad.CtrlRing.TxDmaIdx=2;
  for(unsigned i=0;i<4;i++){
   RTMP_DMACB *c=&ad.CtrlRing.Cell[i];c->AllocVa=descriptors[i];c->AllocSize=16;
   c->pNdisPacket=(void *)(uintptr_t)(i+1);c->PacketPa=i;live[i]=mapped[i]=1;
   TXD_STRUC *tx=(TXD_STRUC *)descriptors[i];tx->SDPtr0=i;tx->SDLen0=32;tx->LastSec0=1;tx->DMADONE=i%2;
  }
  switch(fault){case 2:ad.CtrlRing.Cell[3].AllocVa=NULL;break;
   case 3:ad.CtrlRing.Cell[3].pNextNdisPacket=(void *)7;break;
   case 4:((TXD_STRUC *)descriptors[3])->SDPtr0=123;break;
   case 5:((TXD_STRUC *)descriptors[3])->SDLen1=1;break;
   case 6:ad.CtrlRing.Cell[3].pNdisPacket=ad.CtrlRing.Cell[0].pNdisPacket;break;
   case 8:ad.CtrlRing.TxDmaIdx=4;break;
   case 9:ad.CtrlDescRing.AllocSize=1;break;
   case 11:ad.CtrlRing.Cell[3].PacketPa=1ULL<<32;break;}
  int ret=wr_iot_mcu_boot_control_retire(&ad);assert(ret==(fault?1:0)&&!held);
  int committed=!fault||fault==10;
  assert(unmaps==(committed?4u:0)&&frees==unmaps&&barriers==(unsigned)committed);
  assert(ad.CtrlRing.TxCpuIdx==3&&ad.CtrlRing.TxSwFreeIdx==1&&ad.CtrlRing.TxDmaIdx==(fault==8?4u:2u));
  for(unsigned i=0;i<4;i++){
   assert(live[i]==(unsigned)!committed&&mapped[i]==live[i]);
   if(committed){assert(!ad.CtrlRing.Cell[i].pNdisPacket);assert(((TXD_STRUC *)descriptors[i])->DMADONE);assert(descriptors[i][0]==0&&descriptors[i][2]==0&&descriptors[i][3]==0);}
  }
  if(committed){assert(wr_iot_mcu_boot_control_retire(&ad)==0);assert(unmaps==4&&frees==4);}
 }
 puts("PASS actual control retirement: completed/pending cells, full preflight, packet/DMA identity, malformed/alias refusal, postcommit failure and repeat cleanup; SDK TXD, reduced geometry, DMA injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-control-retire-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
