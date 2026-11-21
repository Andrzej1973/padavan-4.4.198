#!/usr/bin/env python3
"""Host execute actual kernel readback body with capability/copy/MTD actors."""
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
shared = here.parent / 'band-steering'
original = Path(sys.argv[1]).read_text()
ordered = runpy.run_path(str(shared/'prepare-nvram-commit-order.py'))['prepare'](original)
prepared = runpy.run_path(str(shared/'prepare-nvram-flash-readback.py'))['prepare'](ordered)
assert 'case WR_NVRAM_IOCTL_READ_FLASH:' in prepared
start = prepared.index('static long\nwr_nvram_user_read_flash(')
end = prepared.index('\n}', start)+2
prefix = r'''
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
#include "config-bcmnvram.h"
#define __user
#define CAP_SYS_ADMIN 21
#define GFP_KERNEL 0
#define MTD_NVRAM_NAME "Config"
static int nvram_major=1,nvram_sem;
static int privileged=1,bad_in,bad_out,no_mem,read_error,held,reads,copies,frees;
static int capable(int cap){assert(cap==21);return privileged;}
static int copy_from_user(void *to,const void *from,size_t n){if(bad_in)return 1;memcpy(to,from,n);return 0;}
static int copy_to_user(void *to,const void *from,size_t n){copies++;if(bad_out)return 1;memcpy(to,from,n);return 0;}
static void *kzalloc(size_t n,int flags){(void)flags;return no_mem?NULL:calloc(1,n);}
static void kfree(void *p){size_t i;for(i=0;i<NVRAM_SPACE;i++)assert(!((unsigned char*)p)[i]);frees++;free(p);}
static void mutex_lock(int *m){(void)m;assert(!held);held=1;}
static void mutex_unlock(int *m){(void)m;assert(held);held=0;}
static int ra_mtd_read_nm(const char *name,int off,size_t n,unsigned char *p){
 assert(!strcmp(name,"Config")&&off==4096&&n==NVRAM_SPACE&&held);reads++;memset(p,42,n);return read_error;
}
'''
suffix = r'''
static void reset(void){
 assert(!held);privileged=1;nvram_major=1;
 bad_in=bad_out=no_mem=read_error=reads=copies=frees=0;
}
int main(void){
 char out[NVRAM_SPACE];anvram_ioctl_t q={sizeof(q),0,0,NVRAM_SPACE,NULL,out},bad;int i;
 reset();assert(!wr_nvram_user_read_flash(&q));assert(reads==1&&copies==1&&frees==1&&!held);
 for(i=0;i<NVRAM_SPACE;i++)assert(out[i]==42);
 reset();privileged=0;assert(wr_nvram_user_read_flash(&q)==-EPERM&&!reads&&!copies);
 reset();bad_in=1;assert(wr_nvram_user_read_flash(&q)==-EFAULT&&!reads);
 reset();assert(wr_nvram_user_read_flash(NULL)==-EFAULT&&!reads);
 reset();nvram_major=-1;assert(wr_nvram_user_read_flash(&q)==-EAGAIN&&!reads);
 reset();no_mem=1;assert(wr_nvram_user_read_flash(&q)==-ENOMEM&&!reads&&!frees);
 reset();read_error=-EIO;assert(wr_nvram_user_read_flash(&q)==-EIO&&reads==1&&!copies&&frees==1);
 reset();read_error=1;assert(wr_nvram_user_read_flash(&q)==-EIO&&!copies&&frees==1);
 reset();bad_out=1;assert(wr_nvram_user_read_flash(&q)==-EFAULT&&frees==1&&!held);
 for(i=0;i<6;i++){
  reset();bad=q;
  switch(i){case 0:bad.size--;break;case 1:bad.is_temp=1;break;case 2:bad.len_param=1;break;
   case 3:bad.param=out;break;case 4:bad.len_value--;break;case 5:bad.value=NULL;break;}
  assert(wr_nvram_user_read_flash(&bad)==-EINVAL&&!reads&&!copies&&!frees);
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-native-flash-') as directory:
    source = Path(directory)/'check.c'
    binary = Path(directory)/'check'
    source.write_text(prefix+prepared[start:end]+suffix)
    subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2',
                    '-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here/'fixtures'),
                    str(source),'-o',str(binary)],check=True)
    subprocess.run([str(binary)],check=True,timeout=15)
    native = Path(directory)/'sdk/trunk/linux-4.4.x/drivers/nvram/nvram_linux.c'
    native.parent.mkdir(parents=True)
    native.write_text(ordered)
    refused=subprocess.run([sys.executable,str(shared/'prepare-nvram-flash-readback.py'),
                            str(Path(directory)/'sdk')],capture_output=True)
    assert refused.returncode and native.read_text()==ordered
    assert not (native.parent/'wr-nvram-flash-wire.h').exists()
    native.with_name('nvram.c').write_bytes((here/'fixtures/config-native-getall.c').read_bytes())
    subprocess.run([sys.executable,str(shared/'prepare-nvram-snapshot.py'),
                    '--kernel-root',str(Path(directory)/'sdk/trunk/linux-4.4.x')],check=True)

    subprocess.run([sys.executable,str(shared/'prepare-nvram-flash-readback.py'),
                    str(Path(directory)/'sdk')],check=True)
    assert native.read_text()==prepared
    header=native.parent/'wr-nvram-flash-wire.h'
    assert header.read_bytes()==(here/'native-flash-wire.h').read_bytes()
    before=native.read_bytes()
    refused=subprocess.run([sys.executable,str(shared/'prepare-nvram-flash-readback.py'),
                            str(Path(directory)/'sdk')],capture_output=True)
    assert refused.returncode and native.read_bytes()==before

print('PASS actual prepared kernel handler: capability, fixed target, mutex, native errors, allocation/copy failures, bounded request and wiped buffer; host actors only')
