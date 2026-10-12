#!/usr/bin/env python3
"""Test the actual emitted HTTP ZRAM handler with isolated proc input."""
import argparse
import ast
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
tree = ast.parse(Path(__file__).with_name('prepare-zram-status-web.py').read_text())
code = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'code' for t in n.targets))
prefix = r'''
#define SUPPORT_ZRAM 1
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
typedef FILE *webs_t;
static int requested;
static const char *input;
static char observed[32];
static FILE *mock_open(const char *path,const char *mode) {
 FILE *fp;assert(!strcmp(path,"/proc/swaps"));assert(!strcmp(mode,"r"));
 if(!input)return NULL;
 fp=tmpfile();assert(fp);assert(fputs(input,fp)>=0);rewind(fp);return fp;
}
static int nvram_get_int(const char *key){assert(!strcmp(key,"zram_enable"));return requested;}
static int websWrite(webs_t wp,const char *format,...) {
 va_list args;int result;(void)wp;va_start(args,format);
 result=vsnprintf(observed,sizeof(observed),format,args);va_end(args);return result;
}
#define fopen mock_open
'''
suffix = r'''
static void check(int mode,const char *data,const char *expected) {
 requested=mode;input=data;observed[0]=0;
 ej_wr_zram_state(0,NULL,0,NULL);assert(!strcmp(observed,expected));
}
int main(void) {
 const char *empty="Filename Type Size Used Priority\n";
 const char *active="Filename Type Size Used Priority\n/dev/zram0 partition 32768 0 32767\n";
 check(0,empty,"0");check(1,empty,"2");check(2,active,"1");check(0,active,"4");
 check(1,NULL,"3");check(0,NULL,"3");check(1,"","3");
 check(0,"invalid\n","3");check(1,"Filename Type Size Used Priority","3");
 check(1,"Filename Type Size Used Priority\n/dev/sda1 partition 32768 0 0\n","2");
 puts("PASS observed ZRAM HTTP states; router/browser execution unverified");return 0;
}
'''
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(prefix + code + suffix)
