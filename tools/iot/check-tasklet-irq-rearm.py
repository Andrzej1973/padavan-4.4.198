#!/usr/bin/env python3
"""Exercise exact tasklet IRQ rearm with injected MMIO and block interleaving."""
import argparse
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('candidate', type=Path)
args = parser.parse_args()
source = (args.candidate / 'os/linux/rt_rbus_pci_drv.c').read_text()
start = source.index('static inline void rt2860_int_enable(')
end = source.index('\n}', start) + 2
helper = source[start:end]
start = source.index('static inline void rt2860_int_disable(')
end = source.index('\n}', start) + 2
helper += '\n' + source[start:end]
code = r'''
#include <assert.h>
#include <errno.h>
#include <pthread.h>
typedef unsigned int UINT32;
typedef unsigned long ULONG;
typedef struct {
 pthread_mutex_t wr_iot_nettask_lock;
 struct { unsigned blocked,poisoned; } wr_iot_nettask_owner;
 unsigned int_disable_mask,int_enable_reg,flags,reg,writes,reads;
} RTMP_ADAPTER;
#define MT_MAC 1
#define RTMP_MAC_PCI 1
#define MT_INT_MASK_CSR 1
#define fRTMP_ADAPTER_INTERRUPT_ACTIVE 1
static _Thread_local int held;
static pthread_mutex_t event=PTHREAD_MUTEX_INITIALIZER;
static pthread_cond_t changed=PTHREAD_COND_INITIALIZER;
static int pause_write,entered,release_write;
#define RTMP_INT_LOCK(l,f) do{(f)=0;assert(!held);assert(!pthread_mutex_lock(l));held=1;}while(0)
#define RTMP_INT_UNLOCK(l,f) do{(void)(f);assert(held);held=0;assert(!pthread_mutex_unlock(l));}while(0)
#define RTMP_SET_FLAG(a,f) ((a)->flags|=(f))
#define RTMP_CLEAR_FLAG(a,f) ((a)->flags&=~(f))
static void write_reg(RTMP_ADAPTER *a,unsigned value){
 assert(held);assert(!a->wr_iot_nettask_owner.blocked);
 assert(!a->wr_iot_nettask_owner.poisoned);
 assert(!pthread_mutex_lock(&event));
 if(pause_write){entered=1;assert(!pthread_cond_broadcast(&changed));
  while(!release_write)assert(!pthread_cond_wait(&changed,&event));}
 assert(!pthread_mutex_unlock(&event));a->reg=value;a->writes++;
}
#define RTMP_IO_WRITE32(a,r,v) do{assert((r)==1);write_reg(a,v);}while(0)
#define RTMP_IO_READ32(a,r,v) do{assert(held&&(r)==1);*(v)=(a)->reg;(a)->reads++;}while(0)
''' + helper + r'''
static void *rearm(void *arg){rt2860_int_enable(arg,1U);return 0;}
int main(void){
 RTMP_ADAPTER a={.wr_iot_nettask_lock=PTHREAD_MUTEX_INITIALIZER,
  .int_disable_mask=3U,.int_enable_reg=3U};pthread_t thread;
 a.wr_iot_nettask_owner.blocked=1;rt2860_int_enable(&a,1U);
 assert(a.int_disable_mask==3U&&!a.writes&&!a.reads&&!a.flags);
 a.wr_iot_nettask_owner.blocked=0;a.wr_iot_nettask_owner.poisoned=1;
 rt2860_int_enable(&a,1U);assert(a.int_disable_mask==3U&&!a.writes&&!a.reads);
 a.wr_iot_nettask_owner.poisoned=0;pause_write=1;
 assert(!pthread_create(&thread,0,rearm,&a));
 assert(!pthread_mutex_lock(&event));
 while(!entered)assert(!pthread_cond_wait(&changed,&event));
 /* A stop cannot acquire its owner lock between admission and MMIO. */
 assert(pthread_mutex_trylock(&a.wr_iot_nettask_lock)==EBUSY);
 release_write=1;assert(!pthread_cond_broadcast(&changed));
 assert(!pthread_mutex_unlock(&event));assert(!pthread_join(thread,0));
 assert(a.reg==1U&&a.writes==1U&&a.reads==1U&&a.flags==1U);
 assert(!pthread_mutex_lock(&a.wr_iot_nettask_lock));
 a.wr_iot_nettask_owner.blocked=1;
 /* Stand-in for a subsequent device mask performed after blocking. */
 a.reg=0;assert(!pthread_mutex_unlock(&a.wr_iot_nettask_lock));
 rt2860_int_enable(&a,2U);
 assert(!a.reg&&a.writes==1U&&a.reads==1U&&a.int_disable_mask==2U);
 rt2860_int_disable(&a,1U);
 assert(!a.reg&&a.writes==1U&&a.reads==1U&&a.int_disable_mask==2U);
 a.wr_iot_nettask_owner.blocked=0;
 rt2860_int_disable(&a,1U);
 assert(!a.reg&&a.writes==2U&&a.reads==2U&&a.int_disable_mask==3U&&!a.flags);
 a.wr_iot_nettask_owner.poisoned=1;
 rt2860_int_disable(&a,2U);
 assert(a.writes==2U&&a.reads==2U&&a.int_disable_mask==3U);
 assert(!held);return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-tasklet-rearm-') as directory:
    root = Path(directory)
    (root / 'check.c').write_text(code)
    subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-pthread',
                    '-fsanitize=address,undefined', str(root / 'check.c'),
                    '-o', str(root / 'check')], check=True)
    subprocess.run([str(root / 'check')], check=True)
print('PASS tasklet rearm: blocked/poisoned refusal and serialized MMIO; '
      'injected host test, not terminal IRQ/DMA proof')
