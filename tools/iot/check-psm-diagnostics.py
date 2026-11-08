#!/usr/bin/env python3
"""Compile actual generated diagnostic header OFF/ON with injected kernel APIs."""
import ast,subprocess,tempfile
from pathlib import Path
here=Path(__file__).resolve().parent
tree=ast.parse((here/'prepare-psm-diagnostics.py').read_text())
header=next(n.value.value for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='header' for t in n.targets))
with tempfile.TemporaryDirectory(prefix='wr-psm-header-check-') as d:
 root=Path(d);(root/'linux').mkdir();(root/'diag.h').write_text(header)
 (root/'linux/atomic.h').write_text('typedef struct {unsigned v;} atomic_t;\n#define ATOMIC_INIT(x) {x}\nstatic inline int atomic_inc_return(atomic_t *v){return ++v->v;}\n')
 (root/'linux/ratelimit.h').write_text('#define HZ 100\n#define DEFINE_RATELIMIT_STATE(n,i,b) int n=0\nstatic inline int __ratelimit(int *v){return ++*v<=8;}\n')
 pre='''#include <assert.h>
#include <stdarg.h>
#define KERN_INFO ""
static unsigned lines,last_hits;
int printk(const char *fmt,...){
 va_list ap;unsigned e,b,p,x,y;const char *site;(void)fmt;
 va_start(ap,fmt);e=va_arg(ap,unsigned);b=va_arg(ap,unsigned);p=va_arg(ap,unsigned);
 x=va_arg(ap,unsigned);y=va_arg(ap,unsigned);last_hits=va_arg(ap,unsigned);site=va_arg(ap,const char *);va_end(ap);
 assert(e==0&&b==2&&p==1&&x==0&&y==1&&site);lines++;return 0;
}
#include "diag.h"
'''
 for mode in ['off','on']:
  body='int main(void){int x=0;wr_iot_ps_diag(0,2,1,++x,1);assert(!x&&!lines);return 0;}' if mode=='off' else 'int main(void){unsigned i;for(i=0;i<20;i++)wr_iot_ps_diag(0,2,1,0,1);assert(lines==8&&last_hits==8);wr_iot_ps_diag(99,0,0,0,0);assert(lines==8);return 0;}'
  (root/'t.c').write_text(pre+body)
  cmd=['gcc','-std=gnu89','-Wall','-Wextra','-Werror','-fsanitize=address,undefined','-fno-pie','-no-pie','-I'+d,str(root/'t.c'),'-o',str(root/'t')]
  if mode=='on':cmd+=['-DWR_IOT_PSM_DIAG']
  subprocess.run(cmd,check=True);subprocess.run([str(root/'t')],check=True)
  print('PASS actual diagnostic header',mode,'(kernel APIs injected; not target proof)')
