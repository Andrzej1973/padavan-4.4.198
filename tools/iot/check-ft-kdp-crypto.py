#!/usr/bin/env python3
"""Execute checked native KDP crypto bodies and actual ioctl case fragment."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
compose=runpy.run_path(str(here/'ft-kdp-crypto-composition.py'))['compose']
source=(a.source/'ap/ap_ftkd.c').read_text(encoding='latin1')
io=(a.source/'ap/ap_cfg.c').read_text(encoding='latin1')
start=io.index('\t\tcase RT_FT_DATA_ENCRYPT:');end=io.index('\n\t\tcase RT_OID_802_11R_INFO:',start)
fragment=io[start:end]
code,changed=compose(source,fragment)
for invalid in (changed,fragment.replace('FT_KDP_DataDecrypt(', 'changed(',1)):
 try:compose(source,invalid)
 except ValueError:pass
 else:raise AssertionError('duplicate or drift accepted')
prefix=r'''
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include "ft-cache-lifetime.h"
#define VOID void
#define TYPE_FUNC
#define IN
#define INOUT
#define TRUE 1
#define FALSE 0
#define DOT11R_FT_SUPPORT 1
#define FT_KDP_KEY_ENCRYPTION_EXTEND 8
#define DBGPRINT(level,args) ((void)0)
typedef unsigned char UCHAR;typedef unsigned int UINT,UINT32;typedef int BOOLEAN;
typedef struct {UCHAR CryptKey[16];} BLOCK;
typedef struct {struct wr_ft_cache_lifetime wr_ft_cache_lifetime;
 int wr_ft_cache_lifetime_initialized,wr_ft_cache_lifetime_lock;
 struct {struct {int FlgIsFtKdpInit,FT_KdpLock;BLOCK *pFT_KDP_Ctrl_BK;} FtTab;} ApCfg;} RTMP_ADAPTER;
#define PRTMP_ADAPTER RTMP_ADAPTER *
#define FT_KDP_CB (pAd->ApCfg.FtTab.pFT_KDP_Ctrl_BK)
static int held,fail_inner,zero_output,crypto_calls,allocations,frees,copied,close_in_crypto,oversize_output;
static void lock(int *p){assert(!held&&!*p);*p=held=1;}
static void unlock(int *p){assert(held&&*p);*p=held=0;}
#define RTMP_SEM_LOCK(p) lock(p)
#define RTMP_SEM_UNLOCK(p) unlock(p)
static void allocate(RTMP_ADAPTER *ad,UCHAR **out,size_t size){
 assert(!held);
 if(fail_inner&&ad->wr_ft_cache_lifetime.owner.transactions){*out=NULL;return;}
 *out=calloc(1,size);assert(*out);allocations++;
}
static void release(RTMP_ADAPTER *ad,void *ptr){(void)ad;assert(!held&&ptr);free(ptr);frees++;}
#define FT_MEM_ALLOC(ad,out,size) allocate(ad,out,size)
#define FT_MEM_FREE(ad,ptr) release(ad,ptr)
#define NdisZeroMemory(p,n) memset(p,0,n)
#define NdisMoveMemory(p,q,n) memcpy(p,q,n)
static RTMP_ADAPTER *observed;
static void crypto(UCHAR *data,UINT32 length,UCHAR *key,int keylen,UCHAR *out,UINT *outlen){
 assert(key!=observed->ApCfg.FtTab.pFT_KDP_Ctrl_BK->CryptKey);
 assert(key[0]==7);observed->ApCfg.FtTab.pFT_KDP_Ctrl_BK->CryptKey[0]=99;
 assert(key[0]==7);assert(keylen==16&&!held&&observed->wr_ft_cache_lifetime.owner.transactions==1);
 crypto_calls++;
 if(close_in_crypto){
  assert(wr_ft_cache_close(&observed->wr_ft_cache_lifetime));
  assert(!wr_ft_cache_destroy_begin(&observed->wr_ft_cache_lifetime));
 }
 *outlen=zero_output?0:oversize_output?length+16:length;
 if(!zero_output&&!oversize_output)memcpy(out,data,length);
}
#define AES_Key_Wrap crypto
#define AES_Key_Unwrap crypto
#define RT_FT_DATA_ENCRYPT 1
#define RT_FT_DATA_DECRYPT 2
static int copy_from_user(void *out,const void *in,size_t n){memcpy(out,in,n);return 0;}
static int copy_to_user(void *out,const void *in,size_t n){copied++;memcpy(out,in,n);return 0;}
struct request {struct {struct {unsigned int length;void *pointer;}data;}u;};
'''
main=r'''
static int ioctl_case(RTMP_ADAPTER *pAd,int cmd,struct request *wrq){
 int Status=0;
 switch(cmd){
'''+changed+r'''
 default:assert(0);
 }
 return Status;
}
int main(void){
 for(int cmd=1;cmd<=2;cmd++)for(int scenario=0;scenario<8;scenario++){
  RTMP_ADAPTER ad={0};BLOCK block={{0}};UCHAR data[32]={42};
  struct request request={.u.data={.length=16,.pointer=data}};
  unsigned long serial;int before=crypto_calls,copy_before=copied;
  block.CryptKey[0]=7;observed=&ad;wr_ft_cache_lifetime_init(&ad.wr_ft_cache_lifetime);
  ad.wr_ft_cache_lifetime_initialized=1;
  ad.ApCfg.FtTab.FlgIsFtKdpInit=1;ad.ApCfg.FtTab.pFT_KDP_Ctrl_BK=&block;
  serial=wr_ft_cache_start(&ad.wr_ft_cache_lifetime);
  assert(serial&&wr_ft_cache_publish(&ad.wr_ft_cache_lifetime,serial,1));
  oversize_output=scenario==7;fail_inner=scenario==2;zero_output=scenario==3;close_in_crypto=scenario==5;
  if(scenario==1)assert(wr_ft_cache_close(&ad.wr_ft_cache_lifetime));
  if(scenario==4)ad.ApCfg.FtTab.FlgIsFtKdpInit=0;
  if(scenario==6)ad.ApCfg.FtTab.pFT_KDP_Ctrl_BK=NULL;
  int status=ioctl_case(&ad,cmd,&request);
#ifdef FT_KDP_EMPTY
  assert(status==-EAGAIN&&!request.u.data.length&&copied==copy_before);
  assert(crypto_calls==before);
#else
  if(scenario==0||scenario==5){assert(!status&&request.u.data.length==16&&copied==copy_before+1&&data[0]==42);}
  else assert(status==-EAGAIN&&!request.u.data.length&&copied==copy_before);
  assert(crypto_calls==before+((scenario==0||scenario==3||scenario==5||scenario==7)?1:0));
#endif
  assert(!held&&!ad.wr_ft_cache_lifetime.owner.transactions);
  assert(allocations==frees);
 }
 puts("PASS | FT KDP crypto/ioctl | actual native bodies and ioctl fragment; refusal no copy, allocation/zero-output cleanup, lease drain exclusion, native success retained; crypto primitive substituted");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-kdp-crypto-') as td:
 c=Path(td)/'check.c';c.write_text(prefix+code+main)
 for flags in ([],['-DFT_KDP_EMPTY']):
  exe=Path(td)/('empty' if flags else 'normal')
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-unused-function','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),*flags,str(c),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
