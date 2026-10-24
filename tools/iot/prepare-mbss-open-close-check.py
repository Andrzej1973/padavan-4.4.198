#!/usr/bin/env python3
"""Final MBSS open/close + real candidate down bookkeeping; IO is synthetic."""
import argparse,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('driver',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
if a.output.exists():raise SystemExit('New fixture required')
intermediate=a.output.with_suffix('.open.c')
subprocess.run([sys.executable,str(Path(__file__).with_name('prepare-mbss-admission-check.py')),str(a.driver),str(intermediate)],check=True)
s=intermediate.read_text();s=s[:s.index('int main(void){')]
s=s.replace('struct device *net_dev;struct wr_iot_interface_ref','struct device *net_dev;unsigned int VirtualIfCnt;struct {int BssidNum;} ApCfg;struct wr_iot_interface_ref')
s=s.replace('typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;','typedef struct device {PRTMP_ADAPTER ad;} *PNET_DEV;\ntypedef struct adapter RTMP_ADAPTER;')
old='#define VIRTUAL_IF_UP(ad) ((void)(ad),assert(!held),up_error)'
if s.count(old)!=1:raise SystemExit('Changed UP fixture primitive')
s=s.replace(old,'#define VIRTUAL_IF_UP(ad) (assert(!held),up_error?up_error:(((PRTMP_ADAPTER)(ad))->VirtualIfCnt++,0))')
s=s.replace('assert(ad->wr_iot_transition.busy==WR_RADIO_BSS_OPEN);','assert((command==4&&(ad->wr_iot_transition.busy==WR_RADIO_BSS_CLOSE||ad->wr_iot_transition.busy==WR_RADIO_CLOSE))||(command!=4&&ad->wr_iot_transition.busy==WR_RADIO_BSS_OPEN));')
extra=r'''
typedef unsigned int UINT32;
#define MT_MAC 1
#define RTMP_PCI_SUPPORT 1
#define MAX_MBSSID_NUM(ad) 16
#define NDIS_STATUS_FAILURE 1
#define CMD_RTPRIV_IOCTL_MBSS_CR_DISABLE 4
#define RTMP_OS_NETDEV_STOP_QUEUE(dev) ((void)(dev),assert(!held))
#define RT_MOD_HNAT_DEREG(dev) ((void)(dev),assert(!held))
#define VIRTUAL_IF_NUM(ad) ((ad)->VirtualIfCnt)
#define VIRTUAL_IF_DEC(ad) ((ad)->VirtualIfCnt--)
static int mbss_closes,physical_closes,txs_pending,txs_fault,txs_queries;
static int dma_pending,dma_fault,dma_queries;
static int RT28xx_MBSS_IdxGet(PRTMP_ADAPTER ad,PNET_DEV dev)
{assert(ad&&dev&&!held);return 2;}
static int WrBeaconTxSOutstanding(PRTMP_ADAPTER ad,unsigned int bss)
{assert(ad&&!held&&bss==2);txs_queries++;return txs_fault?-1:txs_pending;}
static int WrBeaconDmaOutstanding(PRTMP_ADAPTER ad,unsigned int bss)
{assert(ad&&!held&&bss==2);dma_queries++;return dma_fault?-1:dma_pending;}
static int MBSS_Close(PNET_DEV dev){assert(dev&&!held);mbss_closes++;return 0;}
static int wr_iot_rt28xx_close_checked(void *dev,const struct wr_iot_radio_ticket *t){assert(dev&&t&&!held);physical_closes++;return 0;}
'''
down=(a.driver/'include/wr-iot-virtual-down.inc').read_text()
close=(a.driver/'include/wr-iot-mbss-close-checked.inc').read_text()
post=r'''
int main(void){
 for(int mode=0;mode<4;mode++){
  struct adapter ad={0};struct device main_dev={&ad},dev={&ad};struct wr_iot_radio_ticket t;
  unsigned long seq=0;
  refs=mbss_closes=physical_closes=txs_pending=txs_fault=txs_queries=0;
  dma_pending=dma_fault=dma_queries=0;
  wr_iot_radio_transition_init(&ad.wr_iot_transition);ad.net_dev=&main_dev;ad.VirtualIfCnt=1;ad.ApCfg.BssidNum=3;
  struct wr_iot_interface_ref *r=wr_iot_registry_add(ad.wr_iot_interface_refs,2,&seq,&dev);assert(r);r->published=1;
  ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  up_error=1;assert(MBSS_VirtualIF_Open(&dev)==-1&&ad.VirtualIfCnt==1&&!refs&&r->phase==WR_REF_IDLE);
  ad.wr_iot_transition.phase=WR_RADIO_READY;ad.wr_iot_transition.main_ready=1;
  up_error=0;assert(MBSS_VirtualIF_Open(&dev)==0&&ad.VirtualIfCnt==2&&refs==1&&r->phase==WR_REF_OWNED);
  assert(wr_iot_radio_begin_stop(&ad.wr_iot_transition,ad.VirtualIfCnt,&t));
  if(mode==0||mode==2){
   if(mode==0)txs_pending=1;else dma_pending=1;
   assert(wr_iot_mbss_close_checked(&dev,&t)==-1&&r->close_stage==2U&&
          ad.VirtualIfCnt==2&&refs==1&&mbss_closes==1&&!physical_closes);
   txs_pending=dma_pending=0;
   assert(wr_iot_mbss_close_checked(&dev,&t)==0&&ad.VirtualIfCnt==1&&!refs&&r->phase==WR_REF_IDLE&&mbss_closes==1&&!physical_closes);
   assert(wr_iot_mbss_close_checked(&dev,&t)==0&&ad.VirtualIfCnt==1&&!refs&&mbss_closes==1);
   assert(txs_queries==(mode==0?2:1)&&dma_queries==2);
   assert(wr_iot_radio_finish(&ad.wr_iot_transition,&t,1)&&!held);
  }else{
   if(mode==1)txs_fault=1;else dma_fault=1;
   assert(wr_iot_mbss_close_checked(&dev,&t)==-1&&r->close_stage==5U&&
          ad.VirtualIfCnt==2&&refs==1&&mbss_closes==1&&!physical_closes&&
          txs_queries==(mode==1?1:0)&&dma_queries==1);
   assert(wr_iot_radio_finish_unverified(&ad.wr_iot_transition,&t)&&!held);
  }
 }
 return 0;
}
'''
a.output.write_text(s+extra+down+'\n'+close+post)
print('Extracted final MBSS open/close/down; hardware and OS primitives injected')
