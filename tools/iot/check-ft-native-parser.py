#!/usr/bin/env python3
"""Execute composed native FT parser with explicit field-fill boundary actors."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
native=(a.source/'common/ft.c').read_text()
compose=runpy.run_path(str(here/'ft-parser-bounds-composition.py'))['compose']
text=compose(native)
start=text.index('static VOID FT_ReqActionParse(',text.index('static VOID FT_ReqActionParse(')+1)
parser=text[start:text.index('\n}',start)+2]
prefix='''#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stddef.h>
#include <stdio.h>
#define IN
#define OUT
#define VOID void
#define IE_FT_MDIE 54
#define IE_FT_FTIE 55
#define IE_FT_RIC_DATA 57
#define IE_FT_RIC_DESCRIPTOR 75
#define IE_RSN 48
#define IE_WPA 221
#define FT_R0KH_ID 3
#define FT_ROKH_ID_LEN 48
#define FT_R1KH_ID 1
#define FT_R1KH_ID_LEN 6
#define FT_GTK 2
#define MAX_RICIES_LEN 255
typedef unsigned char UCHAR,*PUCHAR;
typedef unsigned short UINT16;
typedef void *PRTMP_ADAPTER;
typedef struct {unsigned char bytes[3];} FT_MDIE;
typedef struct {unsigned char fixed[82],Option[0];} FT_FTIE;
typedef struct {unsigned char GtkSubIE[64];} FT_FTIE_INFO;
typedef struct {unsigned char Eid,Len,Octet[0];} EID_STRUCT,*PEID_STRUCT;
typedef struct {int MdIeInfo;FT_FTIE_INFO FtIeInfo;
 struct {void *pRicInfo;int Len;unsigned char RicIEs[255];unsigned int RicIEsLen;} RicInfo;
 unsigned char RSNIE_Len,RSN_IE[255];} FT_INFO,*PFT_INFO;
#define NdisZeroMemory(p,n) memset(p,0,n)
#define NdisMoveMemory memcpy
#define NdisEqualMemory(a,b,n) (!memcmp(a,b,n))
#include "ft-request-ie-admission.h"
static unsigned md,ft;
static void FT_FillMdIeInfo(PEID_STRUCT e,int *out){assert(e->Len==3);*out=1;md++;}
static void FT_FillFtIeInfo(PEID_STRUCT e,FT_FTIE_INFO *out){assert(e->Len>=82);(void)out;ft++;}
'''
main='''int main(void){FT_INFO info;
 for(unsigned n=0;n<=257;n++){
  unsigned char *bytes=calloc(1,n?n:1);assert(bytes);
  if(n>=2){bytes[0]=199;bytes[1]=(unsigned char)(n-2);}
  FT_ReqActionParse(NULL,n,bytes,&info);free(bytes);
 }
 unsigned char valid[]={54,3,0,0,0,57,0,199,0};
 FT_ReqActionParse(NULL,sizeof(valid),valid,&info);
 assert(md==1&&info.MdIeInfo==1&&info.RicInfo.Len==4);
 assert(info.RicInfo.RicIEsLen==2);
 unsigned char bad[]={54,3,0,0,0,199};
 FT_ReqActionParse(NULL,sizeof(bad),bad,&info);
 assert(md==1&&!info.MdIeInfo&&!info.RicInfo.pRicInfo);
 unsigned char rsn[]={48,5,0,0,0,15,172};
 FT_ReqActionParse(NULL,sizeof(rsn),rsn,&info);
 assert(info.RSNIE_Len==sizeof(rsn)&&!memcmp(info.RSN_IE,rsn,sizeof(rsn)));
 unsigned char fixed[84]={55,82};FT_ReqActionParse(NULL,sizeof(fixed),fixed,&info);assert(ft==1);
 return 0;}
'''
with tempfile.TemporaryDirectory(prefix='wr-ft-native-parser-') as td:
 src=Path(td)/'check.c';exe=Path(td)/'check';src.write_text(prefix+parser+main)
 subprocess.run(['gcc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-parameter','-Wno-implicit-fallthrough','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+str(here),str(src),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
print('Composed native parser: exact buffers, whole-list refusal, MDIE/FTIE actors, RIC span and OUI copy PASS; full vendor fill/target unverified')
