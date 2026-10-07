"""Extract patched kernel dump logic for bounded host/target checks."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path)
a=p.parse_args();s=(a.source/'trunk/linux-4.4.x/drivers/nvram/nvram.c').read_text()
start=s.index('int\n_nvram_getall(');end=s.index('\n}',start)+2
body=s[start:end]
if 'return -ENOSPC;' not in body: raise ValueError('Overflow candidate not prepared')
test=r'''
#include <assert.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
typedef unsigned int uint;
struct nvram_tuple { const char *name, *value; int val_tmp; struct nvram_tuple *next; };
static struct nvram_tuple *nvram_hash[3];
#define ARRAYSIZE(x) (sizeof(x)/sizeof((x)[0]))
__BODY__
int main(void)
{
 struct { char data[32]; unsigned char guard[8]; } storage;
 struct nvram_tuple second={"aa","bbb",0,0}, first={"a","b",0,0}, temp={"t","x",1,0};
 memset(&storage,0,sizeof(storage));memset(storage.guard,0xA5,sizeof(storage.guard));
 assert(!_nvram_getall(storage.data,2,0) && !storage.data[0] && !storage.data[1]);
 nvram_hash[0]=&first;
 assert(!_nvram_getall(storage.data,5,0) && !memcmp(storage.data,"a=b\0\0",5));
 memset(storage.data,0,sizeof(storage.data));
 assert(_nvram_getall(storage.data,4,0)==-ENOSPC && !storage.data[0]);
 first.next=&second;
 assert(!_nvram_getall(storage.data,12,0) && !memcmp(storage.data,"a=b\0aa=bbb\0\0",12));
 memset(storage.data,0,sizeof(storage.data));
 assert(_nvram_getall(storage.data,11,0)==-ENOSPC);
 nvram_hash[0]=0;nvram_hash[1]=&temp;
 memset(storage.data,0,sizeof(storage.data));
 assert(!_nvram_getall(storage.data,2,0) && !storage.data[0]);
 assert(_nvram_getall(storage.data,4,1)==-ENOSPC);
 assert(!_nvram_getall(storage.data,5,1) && !memcmp(storage.data,"t=x\0\0",5));
 nvram_hash[0]=&first;first.next=0;nvram_hash[1]=0;nvram_hash[2]=&second;
 memset(storage.data,0,sizeof(storage.data));
 assert(_nvram_getall(storage.data,11,0)==-ENOSPC);
 for(uint i=0;i<sizeof(storage.guard);++i)assert(storage.guard[i]==0xA5);
 puts("PASS actual patched kernel dump: exact capacity, overflow rejection, temporary filtering and multiple buckets; kernel locking/runtime not exercised");
 return 0;
}
'''
a.output.mkdir(parents=True,exist_ok=True)
(a.output/'nvram-dump-check.c').write_text(test.replace('__BODY__',body))
