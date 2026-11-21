#!/usr/bin/env python3
"""Execute the pinned native generator before/after actual source preparation.

Small model table/header and rehash/CRC/flash actors exercise the real generator
overflow branch. No kernel allocation, MTD write or device acceptance is claimed.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

here = Path(__file__).resolve().parent
shared = here.parent / "band-steering"
prefix = r'''
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#define NVRAM_SPACE 128
#define NVRAM_MAGIC 0x48534c46
#define NVRAM_VERSION 1
#define SDRAM_INIT 0
#define SDRAM_CONFIG 0
#define SDRAM_REFRESH 0
#define SDRAM_NCDL 0
#define ARRAYSIZE(a) ((int)(sizeof(a)/sizeof((a)[0])))
#define ROUNDUP(n,a) (((n)+(a)-1)&~((a)-1))
struct nvram_header {uint32_t magic,len,crc_ver_init,config_refresh,config_ncdl;};
struct nvram_tuple {const char *name,*value;int val_tmp;struct nvram_tuple *next;};
static struct nvram_tuple tuples[2],*nvram_hash[2];
static int free_calls,restored;static char large[91];
static uint8_t nvram_calc_crc(struct nvram_header *h){(void)h;return 0;}
static void nvram_free(void){free_calls++;nvram_hash[0]=nvram_hash[1]=NULL;}
static void nvram_rehash(struct nvram_header *h){
 char *p=(char *)(h+1);restored=0;
 while(*p){assert(restored<2);nvram_hash[restored]=&tuples[restored];restored++;p+=strlen(p)+1;}
}
static void reset(int overflow){
 memset(large,'x',sizeof(large)-1);large[sizeof(large)-1]=0;
 tuples[0]=(struct nvram_tuple){"a",overflow?large:"one",0,NULL};
 tuples[1]=(struct nvram_tuple){"b",overflow?large:"two",0,NULL};
 nvram_hash[0]=&tuples[0];nvram_hash[1]=&tuples[1];free_calls=restored=0;
}
'''
body = r'''
int main(void){
 union {struct nvram_header align;unsigned char bytes[NVRAM_SPACE];} image={0};
 unsigned char flash[NVRAM_SPACE],before[NVRAM_SPACE];int result;
 reset(1);result=_nvram_generate(&image.align,1);
#if GUARDED
 assert(result==-ENOSPC&&!free_calls&&nvram_hash[0]&&nvram_hash[1]);
#else
 assert(!result&&free_calls==1&&restored==1&&!nvram_hash[1]);
 puts("REPRODUCED pinned native consolidation: overflow returns success and rehash loses a live tuple");
#endif
 reset(1);memset(image.bytes,0,sizeof(image.bytes));memset(flash,0x5a,sizeof(flash));memcpy(before,flash,sizeof(flash));
 result=_nvram_generate(&image.align,0);
 if(!result)memcpy(flash,image.bytes,sizeof(flash)); /* Existing caller commits only success. */
#if GUARDED
 assert(result==-ENOSPC&&!memcmp(flash,before,sizeof(flash))&&!free_calls);
#else
 assert(!result&&memcmp(flash,before,sizeof(flash))&&!free_calls);
 puts("REPRODUCED pinned native flash staging: overflow returns success with an incomplete image");
#endif
 reset(0);memset(image.bytes,0,sizeof(image.bytes));
 assert(!_nvram_generate(&image.align,1)&&free_calls==1&&restored==2);
#if GUARDED
 puts("PASS native prepared generator: overflow preserves live table and staged flash; fitting input still rehashes both tuples; model callbacks only");
#endif
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix="wr-native-overflow-") as directory:
    root = Path(directory)
    source = root / "drivers/nvram/nvram.c"
    source.parent.mkdir(parents=True)
    source.write_bytes((here / "fixtures/config-native-getall.c").read_bytes())
    for guarded in (False, True):
        if guarded:
            subprocess.run([sys.executable, str(shared / "prepare-nvram-snapshot.py"),
                            "--kernel-root", str(root)], check=True)
        text = source.read_text()
        start = text.index("int\n_nvram_generate(")
        end = text.index("\n}", start) + 2
        unit = root / "check.c"
        unit.write_text(prefix + text[start:end] + body)
        binary = root / "check"
        subprocess.run(["gcc", "-std=gnu11", "-Wall", "-Wextra", "-Werror", "-O2",
                        "-fsanitize=address,undefined", "-fno-pie", "-no-pie",
                        "-DGUARDED=" + str(int(guarded)), str(unit), "-o", str(binary)], check=True)
        subprocess.run([str(binary)], check=True, timeout=15)
