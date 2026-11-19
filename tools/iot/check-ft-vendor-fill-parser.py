#!/usr/bin/env python3
"""Execute composed FT parser with native fill routines and extracted SDK types."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
source=(a.source/'common/ft.c').read_text()
text=runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose'](source)
def body(signature):
 starts=[];pos=0
 while True:
  pos=text.find(signature,pos)
  if pos<0:break
  if text.find('{',pos)<text.find(';',pos):starts.append(pos)
  pos+=len(signature)
 assert len(starts)==1,signature
 start=starts[0];return text[start:text.index('\n}',start)+2]
def declaration(text,start,end):
 at=text.index(start);return text[at:text.index(end,at)+len(end)]
wire=(a.source/'include/dot11r_ft.h').read_text(encoding='latin-1')
info=(a.source/'include/ft_cmm.h').read_text(encoding='latin-1')
types=[]
for start,end in [('typedef union GNU_PACKED _FT_CAP_AND_POLICY','} FT_CAP_AND_POLICY, *PFT_CAP_AND_POLICY;'),('typedef struct GNU_PACKED _FT_MDIE','} FT_MDIE, *PFT_MDIE;'),('typedef union GNU_PACKED _FT_MIC_CTR_FIELD','} FT_MIC_CTR_FIELD, *PFT_MIC_CTR_FIELD;'),('typedef struct GNU_PACKED _FT_FTIE','} FT_FTIE, *PFT_FTIE;'),('typedef struct GNU_PACKED _FT_OPTION_FIELD','} FT_OPTION_FIELD, *PFT_OPTION_FIELD;')]:types.append(declaration(wire,start,end))
for name in ('MDIE_INFO','FTIE_INFO','RIC_INFO','INFO'):
 types.append(declaration(info,'typedef struct __FT_'+name,'} FT_'+name+', *PFT_'+name+';'))
prefix='''#include <assert.h>
#include <stddef.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#define IN
#define OUT
#define GNU_PACKED __attribute__((packed))
#define VOID void
typedef unsigned char UCHAR,UINT8,*PUCHAR,*PUINT8;
typedef unsigned short UINT16;
typedef int INT;
typedef void *PVOID,*PRTMP_ADAPTER;
#define FT_MDID_LEN 2
#define FT_MIC_LEN 16
#define FT_NONCE_LEN 32
#define FT_ROKH_ID_LEN 48
#define FT_R1KH_ID_LEN 6
#define FT_R0KH_ID 3
#define FT_R1KH_ID 1
#define FT_GTK 2
#define IE_FT_MDIE 54
#define IE_FT_FTIE 55
#define IE_FT_RIC_DATA 57
#define IE_FT_RIC_DESCRIPTOR 75
#define IE_RSN 48
#define IE_WPA 221
#define MAX_RICIES_LEN 255
#define MAX_LEN_OF_RSNIE 255
#define NdisZeroMemory(p,n) memset(p,0,n)
#define NdisMoveMemory memcpy
#define NdisEqualMemory(a,b,n) (!memcmp(a,b,n))
#define FT_SET_MDID(d,s) memcpy(d,s,2)
#define le2cpu16(x) (x)
#define DBGPRINT(level,args) do{}while(0)
typedef struct {unsigned char Eid,Len,Octet[0];} EID_STRUCT,*PEID_STRUCT;
'''
code=prefix+'\n'.join(types)+'\n#include "ft-request-ie-admission.h"\n'+body('VOID FT_FillMdIeInfo(')+'\n'+body('VOID FT_FillFtIeInfo(')+'\n'+body('static VOID FT_ReqActionParse(')
code+='''
int main(void){FT_INFO out;
 assert(sizeof(FT_MDIE)==3&&offsetof(FT_FTIE,Option)==82&&sizeof(out.FtIeInfo.GtkSubIE)==64);
 for(unsigned n=0;n<=255;n++){
  unsigned char *p=calloc(1,n+2);assert(p);p[0]=IE_FT_FTIE;p[1]=n;
  FT_ReqActionParse(NULL,n+2,p,&out);
  assert((out.FtIeInfo.Len!=0)==(n==82));free(p);
 }
 unsigned char gtk[150]={IE_FT_FTIE,148};gtk[84]=FT_GTK;gtk[85]=64;memset(gtk+86,0x5a,64);
 FT_ReqActionParse(NULL,sizeof(gtk),gtk,&out);assert(out.FtIeInfo.GtkLen==64);
 for(unsigned i=0;i<64;i++)assert(out.FtIeInfo.GtkSubIE[i]==0x5a);
 gtk[85]=65;FT_ReqActionParse(NULL,sizeof(gtk),gtk,&out);assert(!out.FtIeInfo.Len);
 unsigned char md[]={54,3,1,2,0};FT_ReqActionParse(NULL,sizeof(md),md,&out);
 assert(out.MdIeInfo.Len==3&&out.MdIeInfo.MdId[0]==1&&out.MdIeInfo.MdId[1]==2);
 return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-vendor-fill-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(code)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-implicit-fallthrough','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Native FT parser + real MDIE/FTIE fill and SDK type declarations: host PASS; full action/target/runtime pending')
