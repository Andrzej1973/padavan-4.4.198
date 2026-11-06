#!/usr/bin/env python3
"""Execute generated MCUSysInit; loader, scheduler and cleanup are injected."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
text=(a.candidate/'mcu/mcu.c').read_text();start=text.index('INT32 MCUSysInit(');body=text[start:text.index('INT32 MCUSysExit(',start)]
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef int INT32;
#define NDIS_STATUS_SUCCESS 0
#define TRUE 1
#define HIF_MT 1
#define DMA_SCH_LMAC 0
#define DBGPRINT(level,args) ((void)0)
#define DBGPRINT_ERR(args) ((void)0)
struct wr_iot_mcu_boot_ticket {unsigned radio_epoch;};
typedef struct adapter {unsigned wr_iot_boot_active;struct wr_iot_mcu_boot_ticket wr_iot_boot_ticket;struct {int hif_type;} chipCap;struct {void (*FwInit)(struct adapter *);} chipOps;} RTMP_ADAPTER;
static unsigned init_calls,fw_calls,load_calls,scheduler_calls,sdk_calls,abort_calls,fault;
static void init(RTMP_ADAPTER *ad){assert(ad);init_calls++;}
#define MCU_CTRL_INIT(ad) init(ad)
static void fw(RTMP_ADAPTER *ad){assert(ad&&init_calls==1);fw_calls++;}
static int NICLoadFirmware(RTMP_ADAPTER *ad){assert(ad&&init_calls==1);load_calls++;if(fault==4)ad->wr_iot_boot_ticket.radio_epoch++;return fault==1?7:0;}
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
static int wr_iot_mcu_boot_scheduler_run(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(ad&&load_calls==1&&t!=&ad->wr_iot_boot_ticket&&t->radio_epoch==9);scheduler_calls++;return fault==2||fault==4?1:0;}
static int wr_iot_mcu_boot_loader_abort(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(ad&&t&&t->radio_epoch==9);abort_calls++;return 0;}
#endif
#if defined(MT_MAC) && (defined(RTMP_PCI_SUPPORT) || defined(RTMP_USB_SUPPORT))
static int AsicDMASchedulerInit(RTMP_ADAPTER *ad,int mode){assert(ad&&mode==0&&load_calls==1);sdk_calls++;return fault==3?0:1;}
#endif
'''
tail=r'''
int main(void){unsigned owned,hif;
 for(owned=0;owned<2;owned++)for(hif=0;hif<2;hif++)for(fault=0;fault<5;fault++){
 RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=owned;ad.wr_iot_boot_ticket.radio_epoch=9;ad.chipCap.hif_type=hif;ad.chipOps.FwInit=fw;
 init_calls=fw_calls=load_calls=scheduler_calls=sdk_calls=abort_calls=0;
 int bad=fault==1;
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(owned)bad=bad||fault==2||fault==4;
#endif
#if defined(MT_MAC) && (defined(RTMP_PCI_SUPPORT) || defined(RTMP_USB_SUPPORT))
#if defined(MT7603) && defined(RTMP_PCI_SUPPORT)
 if(!owned&&hif&&fault==3)bad=1;
#else
 if(hif&&fault==3)bad=1;
#endif
#endif
 assert(MCUSysInit(&ad)==(bad?-1:0));assert(init_calls==1&&load_calls==1);
#ifdef MT_MAC
 assert(fw_calls==hif);
#else
 assert(!fw_calls);
#endif
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(owned){assert(scheduler_calls==(fault!=1)&&!sdk_calls);assert(abort_calls==(unsigned)bad);}
 else assert(!scheduler_calls&&!abort_calls);
#else
 assert(!scheduler_calls&&!abort_calls);
#endif
 }
 puts("PASS generated MCUSysInit: loader/scheduler failures, exact captured ticket, no double SDK call, ordinary return normalization and build guards; suboperations injected");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-mcu-sys-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+body+tail)
 for flags in ([],['-DMT_MAC','-DRTMP_USB_SUPPORT'],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',td+'/check'],check=True)
  subprocess.run([td+'/check'],check=True)
