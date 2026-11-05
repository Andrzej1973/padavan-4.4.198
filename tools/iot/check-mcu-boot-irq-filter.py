#!/usr/bin/env python3
"""Actual ISR read/filter prefix; downstream source selection/MMIO injected."""
import argparse
from pathlib import Path
import re
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
text=(a.candidate/'os/linux/rt_rbus_pci_drv.c').read_text()
start=text.index('\t\tRTMP_IO_READ32(pAd, MT_INT_SOURCE_CSR, &IntSource);',text.index('VOID RTMPHandleInterrupt('))
end=text.index('\n#ifdef RELEASEEASE_EXCLUDE',start)
actual=text[start:end]
assert text.index('if (IntSource & WF_MAC_INT_3)',end)>end
sdk=(a.candidate/'include/mac/mac_mt/mt_mac_pci.h').read_text()
macros='\n'.join(re.findall(r'^#define\s+(?:MT_INT_R0_DONE|MT_INT_R1_DONE|MT_INT_T5_DONE|MT_INT_RX_DATA|MT_INT_RX_CMD|MT_INT_CMD)\s+.*$',sdk,re.M))
assert len(macros.splitlines())==6
fixture=r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
typedef uint32_t UINT32;
@@MASKS@@
#define MT_INT_SOURCE_CSR 1
#define fRTMP_ADAPTER_NIC_NOT_EXIST 1u
#define fRTMP_ADAPTER_HALT_IN_PROGRESS 2u
typedef struct {unsigned wr_iot_boot_active,flags;} RTMP_ADAPTER;
static unsigned raw,seen,wf_calls,data_calls,rx_calls,tx_calls,reads;
#define RTMP_IO_READ32(ad,reg,out) do{assert(ad&&(reg)==1);reads++;*(out)=raw;}while(0)
#define RTMP_SET_FLAG(ad,f) ((ad)->flags|=(f))
static void dispatch_prefix(RTMP_ADAPTER *pAd){
 UINT32 IntSource;
@@ACTUAL@@
 seen=IntSource;
 if(IntSource&(1u<<27))wf_calls++;
 if(IntSource&MT_INT_RX_DATA)data_calls++;
 if(IntSource&MT_INT_RX_CMD)rx_calls++;
 if(IntSource&MT_INT_CMD)tx_calls++;
}
int main(void){
 for(unsigned boot=0;boot<2;boot++)for(unsigned bit=0;bit<34;bit++){
  RTMP_ADAPTER ad={0};ad.wr_iot_boot_active=boot;
  raw=bit<32?1u<<bit:bit==32?0x7fffffffu:~0u;
  seen=0x12345678;wf_calls=data_calls=rx_calls=tx_calls=reads=0;
  dispatch_prefix(&ad);assert(reads==1);
  if(boot&&raw==~0u){assert(ad.flags==3&&seen==0x12345678&&!wf_calls&&!data_calls&&!rx_calls&&!tx_calls);continue;}
  unsigned expected=boot?raw&(MT_INT_RX_CMD|MT_INT_CMD):raw;
  assert(seen==expected&&!ad.flags);
  assert(wf_calls==!!(expected&(1u<<27))&&data_calls==!!(expected&MT_INT_RX_DATA));
  assert(rx_calls==!!(expected&MT_INT_RX_CMD)&&tx_calls==!!(expected&MT_INT_CMD));
  if(boot)assert(!wf_calls&&!data_calls);
 }
 puts("PASS actual ISR read/filter prefix: all32 sources and mixed pending bits, ordinary unchanged, bootstrap RX1/TX5 only, NIC removal before WF/data; downstream handlers/MMIO injected");
}
'''.replace('@@MASKS@@',macros).replace('@@ACTUAL@@',actual)
with tempfile.TemporaryDirectory(prefix='wr-mcu-irq-filter-') as td:
 c=Path(td)/'check.c';c.write_text(fixture)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',td+'/check'],check=True)
 subprocess.run([td+'/check'],check=True)
