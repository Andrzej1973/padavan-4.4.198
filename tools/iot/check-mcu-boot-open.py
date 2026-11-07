#!/usr/bin/env python3
"""Execute actual NETIF open + internal request client with injected core/IRQ."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
s=(a.candidate/'os/linux/rt_main_dev.c').read_text();start=s.index('int rt28xx_open(VOID *dev)\n{');body=s[start:s.index('\n}',start)+2]
fixture=r'''
#include <assert.h>
#include <errno.h>
#include <stddef.h>
#include <stdio.h>
#include <stdint.h>
#include "peer-open-request.h"
typedef int INT;typedef unsigned UINT;typedef unsigned long ULONG;typedef void VOID;
typedef unsigned long ra_dma_addr_t;typedef unsigned long dma_addr_t;
struct net_device {int dummy;};
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define FALSE 0
#define CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER 0x7f20
#define DBGPRINT(level,args) ((void)0)
#define MTWF_LOG(a,b,c,args) ((void)0)
static int adapter,scenario,order,begin_at,prepare_at,sleep_at,irq_at,init_at,ready_at,fail_at,release_at,opened,irq_init;
static int irq_owned;
static const char *mac="",*hostname="";
#define GET_PAD_FROM_NET_DEV(ad,dev) ((void)(dev),(ad)=&adapter)
static void mode_get(void *ad,ULONG *out){assert(ad==&adapter);*out=0;}
#define RTMP_DRIVER_OP_MODE_GET mode_get
#define RTMP_DRIVER_MCU_SLEEP_CLEAR(ad) ((void)(ad),sleep_at=++order)
#define RTMP_DRIVER_IRQ_INIT(ad) ((void)(ad),irq_init++)
static int load_dev_l1profile(void *ad){assert(ad==&adapter);return 0;}
static int RTMP_COM_IoctlHandle(void *ad,void *wrq,int cmd,unsigned subcmd,void *data,unsigned long size){
 assert(ad==&adapter&&!wrq&&!subcmd&&cmd==CMD_RTPRIV_IOCTL_PEER_OPEN_OWNER&&size==sizeof(struct wr_iot_peer_open_request));
 struct wr_iot_peer_open_request *r=data;
 if(r->action==WR_PEER_OPEN_BEGIN){begin_at=++order;r->serial=11;return scenario==1?1:0;}
 assert(r->serial==11);
 if(r->action==WR_PEER_OPEN_BOOT_PREPARE){prepare_at=++order;return scenario==2?1:0;}
 if(r->action==WR_PEER_OPEN_BOOT_IRQ_READY){ready_at=++order;return scenario==5?1:0;}
 if(r->action==WR_PEER_OPEN_FAIL){fail_at=++order;return 0;}
 return 1;
}
static int RtmpOSIRQRequest(struct net_device *dev){assert(dev);irq_at=++order;if(scenario==3)return -16;irq_owned=1;return 0;}
static int rt28xx_init(void *ad,const char *m,const char *h,const struct wr_iot_peer_open_request *r){
 assert(ad==&adapter&&m==mac&&h==hostname&&r->serial==11&&irq_owned);init_at=++order;return scenario==4||scenario==5?0:1;
}
static void release_irq(void *ad){assert(ad==&adapter&&irq_owned&&ready_at&&fail_at);release_at=++order;irq_owned=0;}
#define RTMP_DRIVER_IRQ_RELEASE release_irq
static void RTMPDrvOpen(void *ad){assert(ad==&adapter&&init_at);opened++;}
'''+(a.candidate/'include/wr-iot-peer-open-client.inc').read_text()+body+r'''
int main(void){
 struct net_device dev;
 for(scenario=0;scenario<=5;scenario++){
  order=begin_at=prepare_at=sleep_at=irq_at=init_at=ready_at=fail_at=release_at=opened=irq_init=irq_owned=0;
  int ret=rt28xx_open(&dev);
  if(!scenario){assert(!ret&&opened==1&&!fail_at&&!release_at&&irq_owned);continue;}
  if(scenario==1){assert(ret==-EBUSY&&!prepare_at&&!irq_at&&!fail_at);continue;}
  assert(ret==-1&&prepare_at>begin_at&&fail_at>ready_at&&!opened);
  if(scenario==2){assert(!sleep_at&&!irq_at&&!release_at);continue;}
  assert(sleep_at>prepare_at&&irq_at>sleep_at);
  if(scenario==3){assert(!init_at&&!irq_init&&!irq_owned&&!release_at);continue;}
  assert(init_at>irq_at&&irq_init==1);
  if(scenario==4)assert(release_at>fail_at&&!irq_owned);
  if(scenario==5)assert(!release_at&&irq_owned);
 }
 puts("PASS actual NETIF open/client: reserve before IRQ, request failure, successful init, ready-before-fail and IRQ release/retention; core/hardware injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-boot-open-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(a.candidate/'include'),str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
