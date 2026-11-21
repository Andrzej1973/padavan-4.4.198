#!/usr/bin/env python3
"""Execute actual preallocated control-ring reset with injected DMA operations."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'common/cmm_mac_pci.c').read_text()
start=s.index('VOID RTMPResetTxRxRingMemory(')
end=s.index('VOID RTMPFreeTxRxRingMemory(',start)
body=s[start:end];start=body.index('#ifdef CONFIG_ANDES_SUPPORT')
block=body[start:body.index('#endif /* CONFIG_ANDES_SUPPORT */',start)]
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define CONFIG_ANDES_SUPPORT 1
#define MGMT_RING_SIZE 8
#define RTMP_PCI_DMA_TODEVICE 1
#define NDIS_STATUS_SUCCESS 0
typedef struct {unsigned SDPtr0,SDPtr1,SDLen0,SDLen1,DMADONE;} TXD_STRUC;
typedef struct packet {unsigned id,unmapped,freed;} *PNDIS_PACKET;
struct cell {void *AllocVa;PNDIS_PACKET pNdisPacket,pNextNdisPacket;};
typedef struct {struct cell Cell[MGMT_RING_SIZE];unsigned TxSwFreeIdx,TxCpuIdx,TxDmaIdx,hw_didx_addr;} RTMP_CTRL_RING;
typedef struct {RTMP_CTRL_RING CtrlRing;} RTMP_ADAPTER;
static unsigned hardware_index,unmaps,frees;
static struct packet packets[MGMT_RING_SIZE*2];
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),(void)(reg),*(out)=hardware_index)
#define INC_RING_INDEX(idx,size) ((idx)=((idx)+1)%(size))
static void unmap(unsigned id,unsigned len){
 assert(id<MGMT_RING_SIZE*2&&len==32&&!packets[id].unmapped&&!packets[id].freed);
 packets[id].unmapped=1;unmaps++;
}
static void release(PNDIS_PACKET pkt){assert(pkt&&pkt->unmapped&&!pkt->freed);pkt->freed=1;frees++;}
#define PCI_UNMAP_SINGLE(ad,ptr,len,dir) ((void)(ad),(void)(dir),unmap(ptr,len))
#define RELEASE_NDIS_PACKET(ad,pkt,status) ((void)(ad),(void)(status),release(pkt))
static void reset(RTMP_ADAPTER *pAd){TXD_STRUC *pTxD;PNDIS_PACKET pPacket;
'''
tail=r'''
}
int main(void){
 for(unsigned first=0;first<MGMT_RING_SIZE;first++)for(unsigned count=0;count<MGMT_RING_SIZE;count++){
  RTMP_ADAPTER ad={0};TXD_STRUC desc[MGMT_RING_SIZE];
  memset(desc,0,sizeof(desc));memset(packets,0,sizeof(packets));unmaps=frees=0;
  ad.CtrlRing.TxSwFreeIdx=first;ad.CtrlRing.TxCpuIdx=(first+count)%MGMT_RING_SIZE;
  hardware_index=first; /* None of the submitted DMA descriptors completed. */
  for(unsigned j=0;j<MGMT_RING_SIZE;j++)ad.CtrlRing.Cell[j].AllocVa=&desc[j];
  for(unsigned j=0;j<count;j++){
   unsigned slot=(first+j)%MGMT_RING_SIZE;
   desc[slot].SDPtr0=slot*2;desc[slot].SDPtr1=slot*2+1;
   desc[slot].SDLen0=desc[slot].SDLen1=32;desc[slot].DMADONE=1;
   ad.CtrlRing.Cell[slot].pNdisPacket=&packets[slot*2];
   ad.CtrlRing.Cell[slot].pNextNdisPacket=&packets[slot*2+1];
  }
  reset(&ad);
  assert(unmaps==count*2&&frees==count*2&&ad.CtrlRing.TxSwFreeIdx==ad.CtrlRing.TxCpuIdx);
  for(unsigned j=0;j<MGMT_RING_SIZE;j++)assert(!ad.CtrlRing.Cell[j].pNdisPacket&&!ad.CtrlRing.Cell[j].pNextNdisPacket);
  reset(&ad);assert(unmaps==count*2&&frees==count*2); /* No repeat unmap/free. */
 }
 puts("PASS actual RESOURCE_PRE_ALLOC control-ring reset: all wrap positions, incomplete DMA, paired packets, empty/repeated cleanup; hardware quiescence is caller prerequisite, not tested");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-ctrl-ring-reset-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+block+'\n#endif\n'+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
