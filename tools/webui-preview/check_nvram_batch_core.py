#!/usr/bin/env python3
"""Actual pinned NVRAM hash/allocator plus isolated batch prototype; host only."""
import hashlib,json,pathlib,subprocess,sys,tarfile,tempfile
here=pathlib.Path(__file__).resolve().parent
with tarfile.open(sys.argv[1]) as archive:
    common=archive.extractfile('trunk/linux-4.4.x/drivers/nvram/nvram.c').read().decode()
    linux=archive.extractfile('trunk/linux-4.4.x/drivers/nvram/nvram_linux.c').read().decode()
    header=archive.extractfile('trunk/linux-4.4.x/include/nvram/bcmnvram.h').read().decode()
def fn(text,marker,prefix=''):
    a=text.index(marker);return prefix+text[a:text.index('\n}',a)+2]+'\n'
prefix=r'''
#define _GNU_SOURCE
#include <assert.h>
#include <errno.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
typedef unsigned int uint;
#define ARRAY_SIZE(a) (sizeof(a)/sizeof((a)[0]))
#define ARRAYSIZE ARRAY_SIZE
#define NVRAM_MAX_PARAM_LEN 64
#define NVRAM_VALUES_SPACE 8192
#define GFP_ATOMIC 0
struct nvram_tuple {char *name,*value;uint32_t val_len:31,val_tmp:1;struct nvram_tuple *next;};
static struct nvram_tuple *nvram_hash[257];
static char arena[NVRAM_VALUES_SPACE],*nvram_values=arena;
static unsigned long nvram_offset;
static int nvram_lock,depth,allocations,live,fail_at;
static pthread_mutex_t host_mutex=PTHREAD_MUTEX_INITIALIZER;
#define spin_lock_irqsave(lock,flags) do{(void)(lock);assert(!pthread_mutex_lock(&host_mutex));assert(!depth);depth=1;(flags)=0;}while(0)
#define spin_unlock_irqrestore(lock,flags) do{(void)(lock);(void)(flags);assert(depth==1);depth=0;assert(!pthread_mutex_unlock(&host_mutex));}while(0)
static void *kmalloc(size_t bytes,int mode){(void)mode;assert(depth==1);allocations++;if(fail_at&&allocations==fail_at)return NULL;void *p=malloc(bytes);if(p)live++;return p;}
static void kfree(void *p){if(p){assert(depth==1);live--;free(p);}}
'''
actual=fn(common,'hash(const char *s)','static inline uint\n')+fn(linux,'_nvram_realloc(struct','struct nvram_tuple *\n')+fn(linux,'_nvram_free(struct','void\n')+fn(common,'_nvram_get(const char *name)\n{','char *\n')+fn(common,'_nvram_set(const char *name, const char *value, int is_temp)\n{','int\n')
fixture=(here/'nvram-batch-fixture.c.inc').read_text()
with tempfile.TemporaryDirectory(prefix='wr-nvram-batch-core-') as scratch:
    root=pathlib.Path(scratch);(root/'fixture.c').write_text(prefix+actual+(here/'nvram-batch-core.c.inc').read_text()+fixture)
    subprocess.run(['gcc','-std=gnu99','-Wall','-Wextra','-Werror','-pthread','-fsanitize=address,undefined','-fno-pie','-no-pie',str(root/'fixture.c'),'-o',str(root/'fixture')],check=True)
    subprocess.run([str(root/'fixture')],check=True)
    size=sum(p.stat().st_size for p in root.iterdir());print('Owned scratch bytes removed',size)
assert not root.exists()
print('Pinned source hashes',json.dumps({'common':hashlib.sha256(common.encode()).hexdigest(),'allocator':hashlib.sha256(linux.encode()).hexdigest(),'header':hashlib.sha256(header.encode()).hexdigest()}))
