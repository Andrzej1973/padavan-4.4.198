#!/usr/bin/env python3
"""Execute generated NICInitializeAdapter failure paths with injected hardware."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
text=(a.candidate/'common/rtmp_init.c').read_text();start=text.index('NDIS_STATUS\tNICInitializeAdapter(');body=text[start:text.index('\nINT rtmp_hif_cyc_init(',start)]
prefix=r'''
#include <assert.h>
#include <stdio.h>
typedef int NDIS_STATUS;typedef unsigned UINT;typedef int BOOLEAN;
#define TRUE 1
#define NDIS_STATUS_SUCCESS 0
#define NDIS_STATUS_FAILURE 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1
#define RTMP_TEST_FLAG(ad,f) ((ad)->flags&(f))
#define DBGPRINT(level,args) ((void)0)
struct wr_iot_mcu_boot_ticket {unsigned radio_epoch;};
typedef struct adapter {unsigned flags,wr_iot_boot_active;struct wr_iot_mcu_boot_ticket wr_iot_boot_ticket;struct {int loadFirmware;} chipOps;} RTMP_ADAPTER;
static unsigned fault,waits,asics,loads,aborts;
static int AsicWaitPDMAIdle(RTMP_ADAPTER *ad,int attempts,int delay){assert(ad&&attempts==100&&delay==1000);waits++;return fault==1?0:1;}
static int NICInitializeAsic(RTMP_ADAPTER *ad,int hard){assert(ad&&hard==1);asics++;if(fault==5)ad->wr_iot_boot_ticket.radio_epoch++;return fault>=2?1:0;}
static int NICLoadFirmware(RTMP_ADAPTER *ad){assert(ad);loads++;return fault==3?1:0;}
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
static int wr_iot_mcu_boot_loader_abort(RTMP_ADAPTER *ad,const struct wr_iot_mcu_boot_ticket *t){assert(ad&&t&&t!=&ad->wr_iot_boot_ticket&&t->radio_epoch==9);aborts++;return 1;}
#endif
'''
tail=r'''
int main(void){unsigned owned,nic;
for(owned=0;owned<2;owned++)for(nic=0;nic<2;nic++)for(fault=0;fault<6;fault++){
 RTMP_ADAPTER ad={0};ad.flags=nic;ad.wr_iot_boot_active=owned;ad.wr_iot_boot_ticket.radio_epoch=9;ad.chipOps.loadFirmware=1;
 waits=asics=loads=aborts=0;unsigned bad=fault>=2||(fault==1&&nic);
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(owned&&fault==1)bad=1;
#endif
 assert(NICInitializeAdapter(&ad,1)==(int)bad);
#if defined(MT7603) && defined(MT_MAC) && defined(RTMP_PCI_SUPPORT)
 if(owned){assert(!loads&&waits==1&&aborts==(fault!=0));if(fault==1)assert(!asics);else assert(asics==1);continue;}
#endif
 assert(!aborts);
 if(fault>=2&&!nic){assert(loads==1);assert(asics==(fault==3?1u:2u));assert(waits==(fault==3?1u:2u));}
 if(fault>=2&&nic)assert(!loads&&asics==1);
 if(fault==1&&nic)assert(!asics);
}
puts("PASS generated post-firmware init: bootstrap DMA/ASIC failure stop, no bootstrap reload, captured ticket, ordinary bounded retry and reload-error propagation; hardware/abort injected");}
'''
with tempfile.TemporaryDirectory(prefix='wr-post-fw-init-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+body+tail)
 for flags in ([],['-DMT7603','-DMT_MAC','-DRTMP_PCI_SUPPORT']):
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',*flags,str(c),'-o',td+'/check'],check=True)
  subprocess.run([td+'/check'],check=True)
