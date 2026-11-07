#!/usr/bin/env python3
"""Extract actual PCI kickout; DMA/register/queue primitives are injected."""
import argparse
from pathlib import Path
p = argparse.ArgumentParser()
p.add_argument('candidate', type=Path)
p.add_argument('output', type=Path)
a = p.parse_args()
if a.output.exists():
    raise SystemExit('Refusing to overwrite output')
source = (a.candidate / 'mcu/andes_mt.c').read_text(encoding='utf-8')
anchor = 'INT32 AndesMTPciKickOutCmdMsg(PRTMP_ADAPTER pAd, struct cmd_msg *msg)'
if source.count(anchor) != 1:
    raise SystemExit('PCI kickout signature changed')
start = source.index(anchor)
end = source.index('\n}', start) + 2
prefix = r'''#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT32;
typedef unsigned long ULONG;
typedef unsigned int UINT32;
typedef unsigned int UINT;
typedef unsigned char UCHAR;
typedef void *PNDIS_PACKET;
typedef int PACKET_INFO;
typedef struct {UINT32 LastSec0,LastSec1,SDLen0,SDLen1,SDPtr0,Burst,DMADONE;} TXD_STRUC;
struct cell {PNDIS_PACKET pNdisPacket,pNextNdisPacket;ULONG PacketPa;void *AllocVa;ULONG AllocPa;};
struct MCU_CTRL {unsigned int flags;int ackq,tx_doneq;};
typedef struct adapter {struct MCU_CTRL MCUCtrl;int CtrlRingLock;struct {UINT32 TxCpuIdx,TxDmaIdx,TxSwFreeIdx,hw_cidx_addr;struct cell Cell[2];} CtrlRing;} *PRTMP_ADAPTER;
struct cmd_msg {PNDIS_PACKET net_pkt;int need_wait,wr_iot_checked,wr_iot_unsubmitted,state;};
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define TRUE 1
#define FALSE 0
#define MCU_INIT 0
#define wait_ack 1
#define tx_done 2
#define MGMT_RING_SIZE 2
#define RT_DEBUG_WARN 0
#define DBGPRINT(level,args) ((void)0)
#define RTMP_PCI_DMA_TODEVICE 0
static int mode,checks,held,queued,writes,mapped,slots;
static unsigned char packet[16];
static int mcu_ready(unsigned int *flags){checks++;if(mode==4&&checks==2)*flags=0;return (*flags&1)!=0;}
#define OS_TEST_BIT(bit,p) ((void)(bit),mcu_ready(p))
#define GET_CTRLRING_FREENO(ad) ((void)(ad),slots)
#define RTMP_SPIN_LOCK_IRQSAVE(lock,flags) ((void)(lock),(void)(flags),assert(!held),held=1)
#define RTMP_SPIN_UNLOCK_IRQRESTORE(lock,flags) ((void)(lock),(void)(flags),assert(held),held=0)
static void RTMP_QueryPacketInfo(PNDIS_PACKET pkt,PACKET_INFO *info,UCHAR **ptr,UINT *len){
 assert(pkt==packet&&held);*info=0;*ptr=mode==2?NULL:packet;*len=sizeof(packet);
}
static ULONG map_packet(PRTMP_ADAPTER ad,UCHAR *ptr,UINT len,int a,int b){
 (void)ad;assert(held&&ptr==packet&&len==sizeof(packet)&&!a&&!b);mapped++;return 4096;
}
#define PCI_MAP_SINGLE map_packet
#define RTMP_DCACHE_FLUSH(a,b) ((void)0)
#define INC_RING_INDEX(index,size) ((index)=((index)+1)%(size))
static void AndesQueueTailCmdMsg(int *queue,struct cmd_msg *msg,int state){
 (void)queue;assert(held&&!msg->wr_iot_unsubmitted);queued++;msg->state=state;
}
#define RTMP_IO_WRITE32(ad,reg,val) ((void)(ad),(void)(reg),(void)(val),assert(held),writes++)
'''
tail = r'''
int main(void){
 struct adapter ad;struct cmd_msg msg;TXD_STRUC descriptor;int result;
 for(mode=0;mode<=4;mode++){
  memset(&ad,0,sizeof(ad));memset(&msg,0,sizeof(msg));memset(&descriptor,0,sizeof(descriptor));
  checks=held=queued=writes=mapped=0;slots=mode==1?0:1;
  ad.MCUCtrl.flags=mode==0?0:1;ad.CtrlRing.Cell[0].AllocVa=&descriptor;
  msg.net_pkt=packet;msg.need_wait=msg.wr_iot_checked=1;
  result=AndesMTPciKickOutCmdMsg(&ad,&msg);assert(!held);
  if(mode<=2){
   assert(result!=0&&msg.wr_iot_unsubmitted&&!mapped&&!queued&&!writes&&!ad.CtrlRing.Cell[0].pNdisPacket);
  }else{
   assert(!msg.wr_iot_unsubmitted&&mapped==1&&queued==1&&ad.CtrlRing.Cell[0].pNdisPacket==packet&&msg.state==wait_ack);
   assert(result==(mode==3?0:-1)&&writes==(mode==3?1:0));
  }
 }
 puts("PASS actual candidate PCI kickout: pre/post ring-ownership failures distinguished; DMA/locks/registers injected, no hardware concurrency proof");
 return 0;
}
'''
a.output.write_text(prefix + source[start:end] + tail, encoding='utf-8')
