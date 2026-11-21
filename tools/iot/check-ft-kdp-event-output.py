#!/usr/bin/env python3
"""Execute actual EventGet caller fragment for all copy/size outcomes."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
source=(a.source/'ap/ap_ftkd.c').read_text(encoding='latin1')
caller=(a.source/'ap/ap_cfg.c').read_text(encoding='latin1')
start=caller.index('FT_KDP_SIGNAL *pFtKdp;')
end=caller.index('\n\t\t\t}',caller.index('/* no event is queued */',start))
fragment=caller[start:end]
compose=runpy.run_path(str(here/'ft-kdp-event-output-composition.py'))['compose']
native,changed=compose(source,fragment)
assert '*pFtKdp=NULL;' in native
for s,c in ((native,changed),(source,fragment.replace('FT_KDP_SIGNAL *pFtKdp;','changed;'))):
 try:compose(s,c)
 except ValueError:pass
 else:raise AssertionError('drift/duplicate accepted')
body=r'''
#include <assert.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <errno.h>
typedef struct {unsigned int EventLen;} FT_KDP_EVT_HEADER;
typedef struct {FT_KDP_EVT_HEADER Content[1];} FT_KDP_SIGNAL;
#define RT_SIGNAL_STRUC_HDR_SIZE 0
#define DBGPRINT(level,args) ((void)0)
static int has_event,fail_copy,copies,frees;
static void FT_KDP_EventGet(void *ad,FT_KDP_SIGNAL **out){
 (void)ad;*out=NULL;if(has_event){*out=calloc(1,sizeof(**out));assert(*out);(*out)->Content[0].EventLen=sizeof(**out);}}
static int copy_to_user(void *out,void *in,size_t n){(void)out;(void)in;(void)n;copies++;return fail_copy;}
static void release(void *ad,void *p){(void)ad;assert(p);frees++;free(p);}
#define FT_MEM_FREE release
struct request {struct {struct {unsigned int length;void *pointer;}data;}u;};
static int output(struct request *wrq){int Status=0;void *pAd=NULL;
'''+changed+r'''
return Status;}
int main(void){
 for(has_event=0;has_event<=1;has_event++)for(fail_copy=0;fail_copy<=1;fail_copy++)for(int capacity=0;capacity<=8;capacity++){
  struct request request={.u.data={.length=(unsigned)capacity,.pointer=NULL}};
  int before=frees,prior=copies;int status=output(&request);
  assert(frees==before+has_event);
  assert(copies==prior+(has_event&&capacity>=(int)sizeof(FT_KDP_SIGNAL)));
  if(!has_event||capacity<(int)sizeof(FT_KDP_SIGNAL)||fail_copy)assert(!request.u.data.length);
  if(has_event&&capacity>=(int)sizeof(FT_KDP_SIGNAL))assert(status==(fail_copy?-EFAULT:0));
 }
 puts("PASS | FT KDP EventGet output | actual caller fragment: absent event, short/exact/large buffer and copy failure release each detached event once");return 0;}
'''
with tempfile.TemporaryDirectory(prefix='ft-event-output-') as td:
 c=Path(td)/'check.c';exe=Path(td)/'check';c.write_text(body)
 subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie',str(c),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
