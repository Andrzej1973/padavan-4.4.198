#!/usr/bin/env python3
"""Actual RX replacement helper with SDK descriptors; allocation/DMA/guards injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
sdk=(a.candidate/'include/mac/mac_mt/mt_mac_pci.h').read_text()
start=sdk.rfind('#ifdef RT_BIG_ENDIAN',0,sdk.index('typedef\tstruct GNU_PACKED _RXD_STRUC'))
end=sdk.index('#endif /* RT_BIG_ENDIAN */',start)+len('#endif /* RT_BIG_ENDIAN */')
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef int INT;typedef uint32_t UINT32;typedef unsigned char UCHAR;typedef void *PNDIS_PACKET;
#define GNU_PACKED __attribute__((packed))
@@LAYOUT@@
#define RX_RING_SIZE 4
#define NUM_OF_RX_RING 2
#define RXD_SIZE 16
#define RX_BUFFER_AGGRESIZE 2048
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define FALSE 0
#define RTMP_PCI_DMA_FROMDEVICE 1
typedef struct {unsigned AllocSize;void *AllocVa;uint64_t AllocPa;} RTMP_DMABUF;
typedef struct {void *AllocVa;PNDIS_PACKET pNdisPacket;RTMP_DMABUF DmaBuf;} RTMP_DMACB;
struct cookie {void *pci_dev;};typedef struct cookie *POS_COOKIE;
typedef struct {void *OS_Cookie;struct {RTMP_DMACB Cell[4];} RxRing[2];} RTMP_ADAPTER;
static unsigned fault,fail_at,allocated,unmapped,released,guard_calls,barriers,heap_live;
static unsigned live[16],mapping[16];static uint32_t descriptors[2][4][4];
#define in_atomic() 0
#define irqs_disabled() 0
#define NdisZeroMemory memset_zero
static void memset_zero(void *p,size_t n){memset(p,0,n);}
#define NdisMoveMemory memcpy
#define RTMP_GetPhysicalAddressHigh(p) ((p)>>32)
#define RTMP_GetPhysicalAddressLow(p) ((UINT32)(p))
#define cpu2le32(v) (v)
#define DMA_MAPPING_ERROR(dev,pa) ((void)(dev),(pa)==UINT64_MAX)
#define wmb() (barriers++)
static int wr_iot_mcu_boot_pse_empty(RTMP_ADAPTER *ad){assert(ad);guard_calls++;return !(fault==4&&guard_calls==2)&&!(fault==5&&guard_calls==3);}
static int wr_iot_mcu_boot_rx_discard_batch(RTMP_ADAPTER *ad,unsigned *empty){assert(ad);*empty=1;return 0;}
static int os_alloc_mem(RTMP_ADAPTER *ad,UCHAR **out,size_t n){assert(ad);if(fault==6)return 1;*out=calloc(1,n);assert(*out);heap_live++;return 0;}
static void os_free_mem(RTMP_ADAPTER *ad,void *p){assert(ad&&heap_live);heap_live--;free(p);}
static PNDIS_PACKET RTMP_AllocateRxPacketBuffer(RTMP_ADAPTER *ad,void *dev,unsigned n,int cached,void **va,uint64_t *pa){
 assert(ad&&dev&&n==2048&&!cached);unsigned id=8+allocated++;
 if(fault==1&&id==8+fail_at)return NULL;
 live[id]=1;*va=(void *)(uintptr_t)(id+1);*pa=id;
 if(fault==2&&id==8+fail_at)*pa=UINT64_MAX;
 else {mapping[id]=1;if(fault==3&&id==8+fail_at)*pa=(1ULL<<32)|id;}
 if(fault==7&&id==8+fail_at)*va=NULL;
 return (void *)(uintptr_t)(id+1);
}
static void unmap(RTMP_ADAPTER *ad,uint64_t pa,unsigned n,int direction){
 assert(ad&&n==2048&&direction==1);unsigned id=(unsigned)pa;assert(id<16&&mapping[id]);mapping[id]=0;unmapped++;
}
#define PCI_UNMAP_SINGLE unmap
static void release(RTMP_ADAPTER *ad,void *pkt,int status){
 (void)status;assert(ad&&pkt);unsigned id=(unsigned)(uintptr_t)pkt-1;
 assert(id<16&&live[id]&&!mapping[id]);live[id]=0;released++;
}
#define RELEASE_NDIS_PACKET release
'''.replace('@@LAYOUT@@',sdk[start:end])+(a.candidate/'include/wr-iot-mcu-boot-rx-refresh.inc').read_text()+r'''
int main(void){
 struct cookie cookie={(void *)1};
 for(fault=0;fault<=7;fault++)for(fail_at=0;fail_at<8;fail_at++){
  RTMP_ADAPTER ad={0};ad.OS_Cookie=&cookie;
  allocated=unmapped=released=guard_calls=barriers=heap_live=0;
  memset(live,0,sizeof(live));memset(mapping,0,sizeof(mapping));memset(descriptors,0xa5,sizeof(descriptors));
  for(unsigned i=0;i<8;i++){
   RTMP_DMACB *c=&ad.RxRing[i/4].Cell[i%4];
   c->AllocVa=descriptors[i/4][i%4];c->pNdisPacket=(void *)(uintptr_t)(i+1);
   c->DmaBuf=(RTMP_DMABUF){2048,(void *)(uintptr_t)(i+1),i};live[i]=mapping[i]=1;
  }
  int ret=wr_iot_mcu_boot_rx_refresh(&ad);assert(ret==(fault?1:0)&&!heap_live);
  int committed=fault==0||fault==5;
  for(unsigned i=0;i<16;i++)assert(live[i]==(committed?(i>=8):(i<8))&&mapping[i]==live[i]);
  for(unsigned i=0;i<8;i++){
   RTMP_DMACB *c=&ad.RxRing[i/4].Cell[i%4];
   assert((uintptr_t)c->pNdisPacket==(committed?i+9:i+1));
   if(committed){RXD_STRUC d;memcpy(&d,c->AllocVa,sizeof(d));assert(d.SDP0==i+8&&d.SDL0==2048&&!d.DDONE&&!d.LS0&&!d.LS1&&!d.SDL1);assert(descriptors[i/4][i%4][3]==0);}
   else assert(descriptors[i/4][i%4][0]==0xa5a5a5a5);
  }
  assert(barriers==(unsigned)committed);
 }
 puts("PASS actual RX refresh: all allocation/mapping/high-address failures, precommit context loss, postcommit refusal, exactly-once unmap/free, SDK descriptors; reduced geometry, DMA injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-rx-refresh-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
