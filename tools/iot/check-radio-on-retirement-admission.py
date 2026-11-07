#!/usr/bin/env python3
"""Execute the generated RadioOn handler with active and retired adapters."""
import argparse
import subprocess
import tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path)
a=p.parse_args()
s=(a.candidate/'common/cmm_cfg.c').read_text()
i=s.index('INT\tSet_RadioOn_Proc(')
f=s[i:s.index('\n}',i)+2]
prefix=r'''
#include <assert.h>
#include <stdlib.h>
#define IN
#define MT7603 1
#define DMA_RESET_SUPPORT 1
#define MT_MAC 1
#define HIF_MT 1
#define TRUE 1
#define FALSE 0
#define DBGPRINT(a,b) ((void)0)
typedef int INT;
typedef unsigned char UCHAR;
typedef unsigned long ULONG;
typedef char RTMP_STRING;
typedef struct {int wr_iot_transition_lock;struct {int retiring;} wr_iot_transition;struct {int hif_type;} chipCap;int iwpriv_command;} *PRTMP_ADAPTER;
static int held,on,off;
#define RTMP_IRQ_LOCK(l,f) do{(void)(l);(f)=0;assert(!held);held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(l);(void)(f);assert(held);held=0;}while(0)
#define simple_strtol strtol
static void MlmeRadioOn(PRTMP_ADAPTER a){(void)a;assert(!held);on++;}
static void MlmeRadioOff(PRTMP_ADAPTER a){(void)a;assert(!held);off++;}
'''
tail=r'''
int main(void){
 struct {int wr_iot_transition_lock;struct {int retiring;} wr_iot_transition;struct {int hif_type;} chipCap;int iwpriv_command;} storage={0};
 PRTMP_ADAPTER a=(void *)&storage;
 a->chipCap.hif_type=HIF_MT;
 assert(Set_RadioOn_Proc(a,"1") && on==1 && !held);
 assert(Set_RadioOn_Proc(a,"0") && off==1 && !held);
 a->wr_iot_transition.retiring=1;a->iwpriv_command=27;
 assert(!Set_RadioOn_Proc(a,"1") && on==1 && a->iwpriv_command==27 && !held);
 assert(!Set_RadioOn_Proc(a,"0") && off==1 && a->iwpriv_command==27 && !held);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-radio-on-check-') as d:
 c=Path(d)/'check.c';exe=Path(d)/'check';c.write_text(prefix+f+tail)
 subprocess.run(['gcc','-std=gnu89','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('PASS generated RadioOn active/retired admission and no mutation on refusal')
