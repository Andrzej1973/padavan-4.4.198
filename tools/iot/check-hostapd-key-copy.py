#!/usr/bin/env python3
"""Execute native key ioctl copy preludes with boundary payload/user-copy actors."""
import argparse,runpy,subprocess,tempfile
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);a=p.parse_args()
here=Path(__file__).resolve().parent
native=(a.source/'ap/ap_cfg.c').read_text()
compose=runpy.run_path(str(here/'hostapd-key-copy-composition.py'))['compose']
prepared=compose(native)
try:compose(prepared)
except ValueError:pass
else:raise AssertionError('duplicate application accepted')
units=[]
for payload,case,typ in [('Key','HOSTAPD_OID_SET_KEY','ieee80211req_key'),('delkey','HOSTAPD_OID_DEL_KEY','ieee80211req_del_key')]:
 start=prepared.index('case '+case+':')
 start=prepared.index('if(wrq->u.data.length',start)
 end=prepared.index('pEntry = MacTableLookup',start)
 end=prepared.index(';',end)+1
 prelude=prepared[start:end]
 prefix='''#include <assert.h>
#include <string.h>
#include <errno.h>
struct ieee80211req_key {unsigned char ik_macaddr[6];};
struct ieee80211req_del_key {unsigned char idk_macaddr[6];};
struct request {struct {struct {unsigned int length;void *pointer;} data;} u;};
static unsigned int copies,lookups,fail_copy;
static int copy_from_user(void *to,void *from,unsigned int size){copies++;if(fail_copy)return 1;memcpy(to,from,size);return 0;}
static void *MacTableLookup(void *ad,unsigned char *mac){(void)ad;(void)mac;lookups++;return (void*)1;}
'''
 body='static int invoke(struct request *wrq){int Status=-EINVAL;void *pAd=0,*pEntry=0;struct '+typ+' '+payload+';switch(1){case 1:\n'+prelude+'\nbreak;} (void)pEntry;return Status;}\n'
 main='''int main(void){struct request q={0};unsigned char data[64]={0};
 assert(invoke(&q)==-EINVAL&&!copies&&!lookups);
 q.u.data.pointer=data;q.u.data.length=1;
 assert(invoke(&q)==-EINVAL&&!copies&&!lookups);
 q.u.data.length=sizeof(struct TYPE);fail_copy=1;
 assert(invoke(&q)==-EFAULT&&copies==1&&!lookups);
 fail_copy=0;assert(!invoke(&q)&&copies==2&&lookups==1);
 return 0;}
'''.replace('TYPE',typ)
 units.append(prefix+body+main)
with tempfile.TemporaryDirectory(prefix='wr-hostapd-copy-') as td:
 for i,code in enumerate(units):
  src=Path(td)/(str(i)+'.c');exe=Path(td)/str(i);src.write_text(code)
  subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-fsanitize=address,undefined','-fno-pie','-no-pie',str(src),'-o',str(exe)],check=True)
  subprocess.run([str(exe)],check=True)
print('Native SET/DEL key copy preludes: malformed/null/copy failure refusal and single-copy success PASS; arbitration unproven')
