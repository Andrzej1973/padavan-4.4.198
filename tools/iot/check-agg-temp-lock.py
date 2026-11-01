#!/usr/bin/env python3
"""Execute exact generated AGG_TEMP lock blocks with injected pthread/MMIO."""
import argparse,re,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('candidate',type=Path);a=p.parse_args()
blocks=[]
for name,count in [('hw_ctrl/cmm_asic_mt.c',6),('common/cmm_mac_pci.c',1),('common/rtmp_init_inf.c',1)]:
 s=(a.candidate/name).read_text()
 found=re.findall(r'\{ ULONG wr_agg_flags;\nRTMP_IRQ_LOCK\(&pAd->wr_iot_agg_temp_lock, wr_agg_flags\);\n.*?\nRTMP_IRQ_UNLOCK\(&pAd->wr_iot_agg_temp_lock, wr_agg_flags\);\n\}',s,re.S)
 assert len(found)==count,(name,len(found))
 assert s.count('RTMP_IO_READ32(pAd, AGG_TEMP,')==count
 for b in found:
  assert b.count('RTMP_IO_READ32')==b.count('RTMP_IO_WRITE32')==1
  assert not any(x in b for x in ['wr_iot_transition_lock','AndesSend','msleep','udelay'])
 blocks+=found
code=r'''
#include <assert.h>
#include <pthread.h>
#include <stdint.h>
typedef unsigned long ULONG;
#define AGG_TEMP 1
struct adapter {pthread_mutex_t wr_iot_agg_temp_lock;uint32_t reg;};
static _Thread_local int held;
#define RTMP_IRQ_LOCK(l,f) do{(f)=0;assert(!held);assert(!pthread_mutex_lock(l));held=1;}while(0)
#define RTMP_IRQ_UNLOCK(l,f) do{(void)(f);assert(held);held=0;assert(!pthread_mutex_unlock(l));}while(0)
#define RTMP_IO_READ32(a,r,v) do{assert(held);*(v)=(a)->reg;}while(0)
#define RTMP_IO_WRITE32(a,r,v) do{assert(held);(a)->reg=(v);}while(0)
'''
for i,b in enumerate(blocks):code+='static void op%d(struct adapter *pAd){uint32_t Value=0,value=0;(void)Value;(void)value;\n%s\n}\n'%(i,b)
code+=r'''
static void *low(void *p){for(int i=0;i<10000;i++)op0(p);return 0;}
static void *high(void *p){for(int i=0;i<10000;i++)op4(p);return 0;}
int main(void){struct adapter a={.wr_iot_agg_temp_lock=PTHREAD_MUTEX_INITIALIZER};pthread_t x,y;
for(unsigned i=0;i<65536;i++){a.reg=0xffff0000U|i;op1(&a);assert(a.reg==(0xffff0000U|(i&~2U)));}
a.reg=0;assert(!pthread_create(&x,0,low,&a));assert(!pthread_create(&y,0,high,&a));assert(!pthread_join(x,0));assert(!pthread_join(y,0));assert(a.reg==0xffff0002U);
op2(&a);op3(&a);op5(&a);op6(&a);op7(&a);assert(a.reg==2U);assert(!held);return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-agg-lock-') as d:
 root=Path(d);(root/'check.c').write_text(code)
 subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-pthread','-fsanitize=address,undefined',str(root/'check.c'),'-o',str(root/'check')],check=True)
 subprocess.run([str(root/'check')],check=True)
print('PASS eight exact AGG_TEMP blocks: lock coverage, conditional unlock, bit preservation, injected concurrent set operations; not real IRQ/MMIO/lifetime proof')