#!/usr/bin/env python3
"""Execute exact original/prepared commit with lock/allocator/MTD actors."""
import pathlib
import runpy
import subprocess
import sys
import tempfile

here = pathlib.Path(__file__).resolve().parent
prepare = runpy.run_path(str(here.parent / 'band-steering/prepare-nvram-commit-order.py'))['prepare']
original = pathlib.Path(sys.argv[1]).read_text()
prepared = prepare(original)
prefix = r'''
#include <assert.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#define NVRAM_SPACE 64
#define GFP_KERNEL 0
#define MTD_NVRAM_NAME "fixture"
#define NVRAM_MTD_OFFSET 4096
#define printk(...) ((void)0)
struct nvram_header {unsigned int word;};
static int nvram_major=1,nvram_sem,nvram_lock;
static int held,allocs,fail_alloc,generation_error,read_error,write_error,same;
static int generates,reads,writes,bad_order;
static void *kzalloc(size_t n,int flags) {
 (void)flags;allocs++;return allocs==fail_alloc?NULL:calloc(1,n);
}
#define kfree free
static void mutex_lock(int *lock){(void)lock;assert(!held);held=1;}
static void mutex_unlock(int *lock){(void)lock;assert(held);held=0;}
#define spin_lock_irqsave(lock,flags) do {(void)(lock);(flags)=0;} while(0)
#define spin_unlock_irqrestore(lock,flags) do {(void)(lock);(void)(flags);} while(0)
static int _nvram_generate(struct nvram_header *p,int temp) {
 (void)temp;generates++;if(!held)bad_order++;
 memset(p,42,NVRAM_SPACE);return generation_error;
}
static int ra_mtd_read_nm(const char *name,int offset,size_t n,unsigned char *p) {
 (void)name;assert(offset==4096&&held);reads++;memset(p,same?42:0,n);return read_error;
}
static int ra_mtd_write_nm(const char *name,int offset,size_t n,unsigned char *p) {
 (void)name;(void)p;assert(offset==4096&&n==64&&held);writes++;return write_error;
}
'''
suffix = r'''
static void reset(void) {
 assert(!held);allocs=fail_alloc=generation_error=read_error=write_error=same=0;
 generates=reads=writes=bad_order=0;nvram_major=1;
}
int main(void) {
 reset();assert(!nvram_commit());assert(generates==1&&reads==1&&writes==1&&!held);
 assert(bad_order==ORIGINAL);
 reset();same=1;assert(!nvram_commit());assert(reads==1&&!writes&&!held);
 reset();generation_error=-ENOSPC;assert(nvram_commit()==-ENOSPC);
 assert(!reads&&!writes&&!held);
 reset();fail_alloc=1;assert(nvram_commit()==-ENOMEM);assert(!generates&&!held);
 reset();fail_alloc=2;assert(!nvram_commit());assert(!reads&&writes==1&&!held);
 reset();read_error=-EIO;assert(!nvram_commit());assert(reads==1&&writes==1&&!held);
 reset();write_error=-EIO;assert(nvram_commit()==-EIO);assert(writes==1&&!held);
 reset();nvram_major=-1;assert(!nvram_commit());assert(!allocs&&!generates&&!held);
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='wr-native-commit-') as directory:
    root = pathlib.Path(directory)
    for label, text in [('original', original), ('prepared', prepared)]:
        start = text.index('int\nnvram_commit(void)')
        end = text.index('\n}', start) + 2
        source = root / (label + '.c')
        binary = root / label
        source.write_text(prefix + text[start:end] + suffix.replace('ORIGINAL', str(int(label == 'original'))))
        subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O2',
                        '-fsanitize=address,undefined', '-fno-pie', '-no-pie',
                        str(source), '-o', str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=15)
    for changed in [original.replace('mutex_lock(&nvram_sem);', ''),
                    original.replace('/* Regenerate NVRAM */', '/* changed */')]:
        try:
            prepare(changed)
        except ValueError:
            pass
        else:
            raise AssertionError('changed native source accepted')
print('PASS exact original exposes pre-mutex generation; prepared serializes snapshot/flash and balances failure/skip/ENOMEM paths; host actors only')
