#!/usr/bin/env python3
"""Extract pinned control-ring retirement; hardware progress is injected."""
import argparse
import hashlib
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('source', type=Path, help='mt76x3 directory')
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise SystemExit('Refusing to overwrite output')
data = (a.source / 'common/cmm_data_pci.c').read_bytes()
if hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest() != '646beb40bc7acb8ee861190b717f8c9a465d0fae':
    raise SystemExit('Unreviewed control-ring source')
text = data.decode('utf-8')
anchor = 'VOID RTMPHandleTxRing8DmaDoneInterrupt(RTMP_ADAPTER *pAd)'
if text.count(anchor) != 1:
    raise SystemExit('Changed handler signature')
start = text.index(anchor)
end = text.index('\n}', start) + 2
prefix = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef void VOID;
typedef unsigned char UCHAR;
typedef void *PNDIS_PACKET;
typedef struct {unsigned int SDPtr0,SDLen0;} TXD_STRUC;
struct cell {void *AllocVa;unsigned long AllocPa;PNDIS_PACKET pNdisPacket;};
typedef struct {unsigned int TxSwFreeIdx,TxDmaIdx,hw_didx_addr;struct cell Cell[2];} RTMP_CTRL_RING;
typedef struct {int CtrlRingLock;RTMP_CTRL_RING CtrlRing;} RTMP_ADAPTER;
#define MGMT_RING_SIZE 2
#define RTMP_PCI_DMA_TODEVICE 0
static int held,unmaps,frees;
static unsigned int hardware_index;
static unsigned char packet;
#define NdisAcquireSpinLock(p) ((void)(p),assert(!held),held=1)
#define NdisReleaseSpinLock(p) ((void)(p),assert(held),held=0)
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),(void)(reg),assert(held),*(out)=hardware_index)
#define PCI_UNMAP_SINGLE(ad,ptr,len,dir) ((void)(ad),assert(held&&(ptr)==4096&&(len)==16&&(dir)==0),unmaps++)
#define RTMPFreeNdisPacket(ad,pkt) ((void)(ad),assert(held&&(pkt)==&packet),frees++)
#define RTMP_DCACHE_FLUSH(a,b) ((void)0)
#define INC_RING_INDEX(i,n) ((i)=((i)+1)%(n))
'''
tail = r'''
int main(void) {
 RTMP_ADAPTER ad;TXD_STRUC descriptors[2];
 memset(&ad,0,sizeof(ad));memset(descriptors,0,sizeof(descriptors));
 for(int i=0;i<2;i++) ad.CtrlRing.Cell[i].AllocVa=&descriptors[i];
 descriptors[0].SDPtr0=descriptors[1].SDPtr0=4096;
 descriptors[0].SDLen0=descriptors[1].SDLen0=16;
 ad.CtrlRing.Cell[0].pNdisPacket=&packet;
 hardware_index=0;
 RTMPHandleTxRing8DmaDoneInterrupt(&ad);
 assert(!held&&!frees&&!unmaps&&ad.CtrlRing.Cell[0].pNdisPacket==&packet);
 hardware_index=1;
 RTMPHandleTxRing8DmaDoneInterrupt(&ad);
 assert(!held&&frees==1&&unmaps==1&&!ad.CtrlRing.Cell[0].pNdisPacket);
 RTMPHandleTxRing8DmaDoneInterrupt(&ad);
 assert(frees==1&&unmaps==1);
 hardware_index=0; /* Empty slot advances across wrap without freeing. */
 RTMPHandleTxRing8DmaDoneInterrupt(&ad);
 assert(!held&&ad.CtrlRing.TxSwFreeIdx==0&&frees==1&&unmaps==1);
 ad.CtrlRing.TxSwFreeIdx=1;ad.CtrlRing.Cell[1].pNdisPacket=&packet;
 RTMPHandleTxRing8DmaDoneInterrupt(&ad);
 assert(!held&&ad.CtrlRing.TxSwFreeIdx==0&&!ad.CtrlRing.Cell[1].pNdisPacket&&frees==2&&unmaps==2);
 puts("PASS pinned control-ring handler: no DMA progress retains packet; progress frees once; empty/wrap cases; hardware and locks injected");
 return 0;
}
'''
a.output.write_text(prefix + text[start:end] + tail, encoding='utf-8')
