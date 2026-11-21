#!/usr/bin/env python3
"""Reproduce the vendor sequence reuse limitation; not an ACK acceptance gate."""
import argparse
from pathlib import Path
import subprocess
import tempfile
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('candidate',type=Path)
a=p.parse_args()
s=(a.candidate/'mcu/andes_core.c').read_text()
i=s.index('static inline UCHAR AndesGetCmdMsgSeq(')
body=s[i:s.index('\n}',i)+2]
prefix='#include <assert.h>\ntypedef unsigned char UCHAR;typedef unsigned char UINT8;\nstruct cmd_msg {int seq;}; struct MCU_CTRL {int ackq_lock,ackq;unsigned char cmd_seq;};\ntypedef struct {struct MCU_CTRL MCUCtrl;} RTMP_ADAPTER;\n#define RTMP_SPIN_LOCK_IRQSAVE(l,f) do{(void)(l);*(f)=0;}while(0)\n#define RTMP_SPIN_UNLOCK_IRQRESTORE(l,f) do{(void)(l);(void)(f);}while(0)\n#define DlListForEach(m,q,t,k) for((m)=0;(m)!=0;)\n#define DBGPRINT(a,b) ((void)0)\n'
tail='int main(void){RTMP_ADAPTER a={0};unsigned char old=AndesGetCmdMsgSeq(&a);assert(old==1);for(int i=0;i<14;i++)assert(AndesGetCmdMsgSeq(&a)!=old);assert(AndesGetCmdMsgSeq(&a)==old);return 0;}\n'
with tempfile.TemporaryDirectory(prefix='wr-mcu-sequence-') as t:
 c=Path(t)/'check.c';exe=Path(t)/'check'
 c.write_text(prefix+body+'\n'+tail)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('REPRODUCED sequence1 reuse at allocation16 with empty ACK queue; does not prove firmware timing or safe ACK correlation')
