#!/usr/bin/env python3
"""Execute the generated SDK scheduler body with bounded MMIO observations."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate', type=Path)
a = p.parse_args()
text = (a.candidate / 'hw_ctrl/cmm_asic_mt.c').read_text()
start = text.index('INT32 wr_iot_boot_sdk_scheduler_checked(')
body = text[start:text.index('\n}\n', start) + 3]
registers = sorted(set(re.findall(r'RTMP_IO_(?:READ|WRITE)32\(pAd,\s*([A-Z][A-Z0-9_]*)', body)))
defines = '\n'.join('#define %s %d' % (name, i + 1) for i, name in enumerate(registers))
prefix = r'''
#include <assert.h>
#include <stdio.h>
typedef unsigned UINT32; typedef int INT32; typedef int INT;
typedef struct { unsigned ap; struct {struct {struct {unsigned AmsduEnable;} field;} BACapability;} CommonCfg; struct {unsigned BssidNum;} ApCfg; } RTMP_ADAPTER;
#define RTMP_PCI_SUPPORT
#define CONFIG_AP_SUPPORT
#define IF_DEV_CONFIG_OPMODE_ON_AP(ad) if((ad)->ap)
#define TRUE 1
#define FALSE 0
#define DMA_SCH_LMAC 0
#define DMA_SCH_BYPASS 1
#define DMA_SCH_HYBRID 2
#define MAX_BEACON_SIZE 512
#define MAX_BMCAST_SIZE 1536
#define MAX_BMCAST_COUNT 3
#define MAX_MCUCMD_SIZE 4096
#define MAX_DATA_SIZE 1792
#define MAX_AMSDU_DATA_SIZE 4096
#define MT7603 0
#define MT7603E1 1
#define MT7603E2 2
static unsigned revision, raw, remap, groups, group0, writes;
#define MTK_REV_GTE(ad,chip,rev) (revision>=(rev))
#define MTK_REV_LT(ad,chip,rev) (revision<(rev))
'''
mmio = r'''
static unsigned observe(unsigned reg){return reg==0x80120?raw:reg==MCU_PCIE_REMAP_2?remap:0;}
static void write_reg(unsigned reg,unsigned val){writes++;if(reg==MCU_PCIE_REMAP_2)remap=val;if(reg==MT_GROUP_THD_0){groups++;group0=val;}}
#define MT_PSE_BASE_ADDR 0x80000000u
#define RTMP_IO_READ32(ad,reg,out) ((void)(ad),*(out)=observe(reg))
#define RTMP_IO_WRITE32(ad,reg,val) ((void)(ad),write_reg(reg,val))
'''
tail = r'''
int main(void){unsigned bssid,amsdu,pages;
 for(revision=1;revision<=2;revision++)for(bssid=1;bssid<=16;bssid++)for(amsdu=0;amsdu<=1;amsdu++)for(pages=0;pages<=160;pages++){
  RTMP_ADAPTER ad={0};unsigned size=128;ad.ap=1;
#ifdef MT7603_FPGA
  size=256;
#endif
  unsigned beacon=512/size*(bssid-1)+(amsdu?4096:1792)/size;
  unsigned command=4096/size;
  unsigned valid=pages&&(revision==1||pages>beacon+command);
  ad.ApCfg.BssidNum=bssid;ad.CommonCfg.BACapability.field.AmsduEnable=amsdu;
  raw=pages<<16;remap=0x12345678;groups=group0=writes=0;
  assert(wr_iot_boot_sdk_scheduler_checked(&ad,DMA_SCH_LMAC)==(int)valid);
  assert(remap==0x12345678);
  assert(groups==valid);
  if(valid)assert(group0==(revision==1?pages:pages-beacon-command));
  if(!valid)assert(writes==2);
 }
 {RTMP_ADAPTER ad={0};ad.ap=1;raw=~0u;remap=0x12345678;writes=groups=0;
 assert(!wr_iot_boot_sdk_scheduler_checked(&ad,DMA_SCH_LMAC));assert(remap==0x12345678&&!groups&&writes==2);}
 {RTMP_ADAPTER ad={0};unsigned mode;writes=0;
 assert(!wr_iot_boot_sdk_scheduler_checked(&ad,DMA_SCH_LMAC));assert(!writes);
 ad.ap=1;
 for(mode=1;mode<=3;mode++){assert(!wr_iot_boot_sdk_scheduler_checked(&ad,mode));assert(!writes);}}
 puts("PASS generated SDK quota: E1/E2, BSSID1..16, AMSDU, zero/all-ones, subtraction boundary and remap restoration (MMIO injected)");
}
'''
with tempfile.TemporaryDirectory(prefix='wr-sdk-quota-') as td:
    source = Path(td) / 'check.c'
    source.write_text(prefix + defines + mmio + body + tail)
    for flags in ([], ['-DMT7603_FPGA']):
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                        '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                        *flags, str(source), '-o', td + '/check'], check=True)
        subprocess.run([td + '/check'], check=True)
