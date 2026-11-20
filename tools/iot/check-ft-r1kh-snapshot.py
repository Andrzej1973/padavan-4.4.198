#!/usr/bin/env python3
"""Execute the generated snapshot API with the pinned native cache entry type."""
import argparse
from pathlib import Path
import runpy
import subprocess
import tempfile

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('source',type=Path)
a=p.parse_args()
here=Path(__file__).resolve().parent
api=runpy.run_path(str(here/'ft-r1kh-snapshot-composition.py'))
source=(a.source/'common/ft.c').read_text()
header=(a.source/'include/ft.h').read_text()
changed,decl=api['compose'](source,header)
assert changed.replace('\n\n'+api['FUNCTION']+'\n','',1)==source
assert decl.replace(api['PROTOTYPE']+'\n\n','',1)==header
try:
    api['compose'](changed,decl)
except ValueError:
    pass
else:
    raise AssertionError('duplicate snapshot preparation accepted')
types=(a.source/'include/ft_cmm.h').read_text()
start=types.index('typedef struct __FT_R1KH_ENTRY')
end=types.index('} FT_R1HK_ENTRY, *PFT_R1HK_ENTRY;',start)+len('} FT_R1HK_ENTRY, *PFT_R1HK_ENTRY;')
prefix=r'''
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
typedef unsigned char UINT8,UCHAR;
typedef unsigned int UINT32;
typedef int BOOLEAN;
#define TRUE 1
#define FALSE 0
#define FT_ROKH_ID_LEN 48
#define FT_KDP_WPA_NAME_MAX_SIZE 16
#define FT_R1KH_HASH_INDEX(name) 0
'''+types[start:end]+r'''
typedef struct {struct {struct {int FT_R1khEntryTabLock,FT_R1khEntryTabReady;
 struct {void *pHead;} FT_R1khEntryTab[1];} FtTab;} ApCfg;} RTMP_ADAPTER;
static FT_R1HK_ENTRY *retire_on_unlock;
static int held;
static void lock_cache(int *lock){assert(!*lock&&!held);*lock=held=1;}
static void unlock_cache(int *lock){assert(*lock&&held);*lock=held=0;
 if(retire_on_unlock){free(retire_on_unlock);retire_on_unlock=NULL;}}
static void copy_locked(void *out,const void *in,size_t n){assert(held);memcpy(out,in,n);}
#define RTMP_SEM_LOCK(p) lock_cache(p)
#define RTMP_SEM_UNLOCK(p) unlock_cache(p)
#define RTMPEqualMemory(a,b,n) (!memcmp(a,b,n))
#define NdisZeroMemory(p,n) memset(p,0,n)
#define NdisMoveMemory(p,q,n) copy_locked(p,q,n)
'''
main=r'''
int main(void){
 RTMP_ADAPTER ad={0};FT_R1HK_ENTRY out;
 unsigned char name[16]={7},miss[16]={8};
 FT_R1HK_ENTRY *first=calloc(1,sizeof(*first)),*second=calloc(1,sizeof(*second));
 assert(first&&second);first->pNext=second;first->PmkR1Name[0]=1;
 memcpy(second->PmkR1Name,name,16);second->PmkR1Key[0]=99;
 second->R0khIdLen=48;second->R0khId[47]=42;second->KeyLifeTime=17;
 ad.ApCfg.FtTab.FT_R1khEntryTab[0].pHead=first;
 memset(&out,0x55,sizeof(out));
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out));
 assert(!out.pNext&&!out.PmkR1Key[0]&&!held);
 ad.ApCfg.FtTab.FT_R1khEntryTabReady=1;
 assert(!wr_ft_r1kh_snapshot(&ad,miss,&out)&&!out.PmkR1Key[0]);
 second->R0khIdLen=49;
 assert(!wr_ft_r1kh_snapshot(&ad,name,&out)&&!out.PmkR1Key[0]);
 second->R0khIdLen=48;
 retire_on_unlock=second;
 assert(wr_ft_r1kh_snapshot(&ad,name,&out));
 /* The matched native node was freed at unlock; no pointer may escape. */
 first->pNext=NULL;
 assert(!out.pNext&&out.PmkR1Key[0]==99&&out.KeyLifeTime==17&&out.R0khId[47]==42&&!held);
 assert(!wr_ft_r1kh_snapshot(NULL,name,&out)&&!out.PmkR1Key[0]);
 assert(!wr_ft_r1kh_snapshot(&ad,NULL,&out)&&!out.PmkR1Key[0]);
 assert(!wr_ft_r1kh_snapshot(&ad,name,NULL)&&!held);
 free(first);
 puts("PASS | FT R1KH snapshot | locked value copy survives immediate node retirement; miss, closed cache, invalid length and null refusal");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='ft-r1kh-snapshot-') as td:
    c=Path(td)/'check.c'
    exe=Path(td)/'check'
    c.write_text(prefix+api['FUNCTION']+main)
    subprocess.run(['gcc','-std=c11','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',str(exe)],check=True)
    subprocess.run([str(exe)],check=True)
print('PASS | FT R1KH snapshot composition | native source preserved, pinned entry type, duplicate refusal; callers unmodified')
