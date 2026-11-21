#!/usr/bin/env python3
"""Execute prepared conditional save with deterministic native lock/MTD actors."""
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
here=Path(__file__).resolve().parent;shared=here.parent/'band-steering'
s=Path(sys.argv[1]).read_text()
s=runpy.run_path(str(shared/'prepare-nvram-commit-order.py'))['prepare'](s)
s=runpy.run_path(str(shared/'prepare-nvram-flash-readback.py'))['prepare'](s)
a=s.index('static int\nwr_nvram_generated_profile_matches(');b=s.index('static long\ndev_nvram_ioctl(',a)
assert 'case WR_NVRAM_IOCTL_SAVE_PROFILE:' in s
prefix=r'''
#include <stdint.h>
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "config-bcmnvram.h"
#include "native-flash-wire.h"
#define __user
#define CAP_SYS_ADMIN 21
#define GFP_KERNEL 0
#define MTD_NVRAM_NAME "Config"
static int nvram_major=228,nvram_sem,nvram_lock;
static int privileged=1,bad_copy,allocs,fail_alloc,frees,held,spinning;
static int reads,writes,generates,generation_error,read_failure,write_failure,corrupt_read,race;
static const char *current="expected",*policy="0",*generated="expected";
static unsigned char flash[NVRAM_SPACE];
static int capable(int cap){assert(cap==21);return privileged;}
static int copy_from_user(void *out,const void *in,size_t n){if(bad_copy)return 1;memcpy(out,in,n);return 0;}
static void *kzalloc(size_t n,int flags){(void)flags;assert(n==NVRAM_SPACE);allocs++;return allocs==fail_alloc?NULL:calloc(1,n);}
static void kfree(void *p){size_t i;for(i=0;i<NVRAM_SPACE;i++)assert(!((unsigned char*)p)[i]);frees++;free(p);}
static void mutex_lock(int *m){(void)m;assert(!held);held=1;if(race==1)policy="1";if(race==2)current="foreign";}
static void mutex_unlock(int *m){(void)m;assert(held&&!spinning);held=0;}
#define spin_lock_irqsave(m,f) do{(void)(m);(f)=0;assert(held&&!spinning);spinning=1;}while(0)
#define spin_unlock_irqrestore(m,f) do{(void)(m);(void)(f);assert(spinning);spinning=0;}while(0)
static const char *_nvram_get(const char *key){assert(held&&spinning);return !strcmp(key,WR_NVRAM_PROFILE_KEY)?current:policy;}
static void fill(unsigned char *out,const char *value){
 struct nvram_header *h=(struct nvram_header*)out;size_t n;
 memset(out,0,NVRAM_SPACE);n=strlen(WR_NVRAM_PROFILE_KEY);
 memcpy(out+sizeof(*h),WR_NVRAM_PROFILE_KEY,n);out[sizeof(*h)+n]='=';
 strcpy((char*)out+sizeof(*h)+n+1,value);
 h->len=(sizeof(*h)+n+1+strlen(value)+2+3)&~3u;
}
static int _nvram_generate(struct nvram_header *out,int temp){assert(held&&spinning&&!temp);generates++;if(generation_error)return generation_error;fill((unsigned char*)out,generated);return 0;}
static int ra_mtd_read_nm(const char *name,int offset,size_t n,unsigned char *out){
 assert(held&&!spinning&&!strcmp(name,"Config")&&offset==4096&&n==NVRAM_SPACE);
 reads++;if(reads==read_failure)return -EIO;memcpy(out,flash,n);if(reads==corrupt_read)out[24]^=1;return 0;
}
static int ra_mtd_write_nm(const char *name,int offset,size_t n,const unsigned char *in){
 assert(held&&!spinning&&!strcmp(name,"Config")&&offset==4096&&n==NVRAM_SPACE);
 writes++;if(write_failure){memcpy(flash,in,n/2);return -EIO;}memcpy(flash,in,n);return 0;
}
'''
suffix=r'''
static struct wr_nvram_save_profile request(void){
 struct wr_nvram_save_profile r={0};r.size=sizeof(r);r.version=1;r.record_length=8;strcpy(r.record,"expected");return r;
}
static void reset(void){
 assert(!held&&!spinning);nvram_major=228;privileged=1;bad_copy=allocs=fail_alloc=frees=0;
 reads=writes=generates=generation_error=read_failure=write_failure=corrupt_read=race=0;
 current=generated="expected";policy="0";memset(flash,0,sizeof(flash));
}
int main(void){
 struct wr_nvram_save_profile r=request(),bad;int i;
 reset();assert(!wr_nvram_user_save_profile(&r));assert(generates==1&&writes==1&&reads==2&&frees==2&&!held);
 reset();fill(flash,"expected");assert(!wr_nvram_user_save_profile(&r));assert(reads==1&&!writes&&frees==2);
 reset();race=1;assert(wr_nvram_user_save_profile(&r)==-EAGAIN&&!generates&&!reads&&!writes&&frees==2);
 reset();race=2;assert(wr_nvram_user_save_profile(&r)==-ESTALE&&!generates&&!reads&&!writes);
 reset();policy="1";r.flags=WR_NVRAM_SAVE_EXPLICIT;assert(!wr_nvram_user_save_profile(&r)&&writes==1);r.flags=0;
 reset();policy="invalid";assert(wr_nvram_user_save_profile(&r)==-EINVAL&&!generates&&!writes);
 reset();generated="excluded-temporary";assert(wr_nvram_user_save_profile(&r)==-ESTALE&&generates==1&&!reads&&!writes);
 reset();generation_error=-ENOSPC;assert(wr_nvram_user_save_profile(&r)==-ENOSPC&&!reads&&!writes&&frees==2);
 reset();read_failure=1;assert(wr_nvram_user_save_profile(&r)==-EIO&&!writes&&reads==1);
 reset();read_failure=2;assert(wr_nvram_user_save_profile(&r)==-EIO&&writes==1&&reads==2);
 reset();write_failure=1;assert(wr_nvram_user_save_profile(&r)==-EIO&&writes==1&&reads==1);
 reset();corrupt_read=2;assert(wr_nvram_user_save_profile(&r)==-EIO&&writes==1);
 for(i=1;i<=2;i++){reset();fail_alloc=i;assert(wr_nvram_user_save_profile(&r)==-ENOMEM&&!generates&&!writes&&frees==1);}
 reset();privileged=0;assert(wr_nvram_user_save_profile(&r)==-EPERM&&!allocs);
 reset();bad_copy=1;assert(wr_nvram_user_save_profile(&r)==-EFAULT&&!allocs);
 reset();assert(wr_nvram_user_save_profile(NULL)==-EFAULT&&!allocs);
 reset();nvram_major=-1;assert(wr_nvram_user_save_profile(&r)==-EAGAIN&&!allocs);
 for(i=0;i<7;i++){
  reset();bad=r;switch(i){case 0:bad.size--;break;case 1:bad.version=2;break;case 2:bad.flags=2;break;
  case 3:bad.record_length=0;break;case 4:bad.record_length=384;break;case 5:bad.record[2]=0;break;case 6:bad.record[8]='x';break;}
  assert(wr_nvram_user_save_profile(&bad)==-EINVAL&&!allocs&&!writes);
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-conditional-save-') as directory:
 root=Path(directory);source=root/'check.c';binary=root/'check';source.write_text(prefix+'\n#define current ((void *)0)\n'+s[a:b]+'\n#undef current\n'+suffix)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined',
 '-fno-pie','-no-pie','-I'+str(here/'fixtures'),'-I'+str(here),str(source),'-o',str(binary)],check=True)
 subprocess.run([str(binary)],check=True,timeout=15)
print('PASS actual conditional kernel save: policy/profile admission races refuse, explicit save, persistent tuple check, one write/readback, unchanged skip, all tested errors unlock/wipe; MTD actors only')
