#!/usr/bin/env python3
"""Execute the emitted DNS process handler with controlled observations."""
import argparse
import ast
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
tree = ast.parse(Path(__file__).with_name('prepare-dns-process-status.py').read_text())
code = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'code' for t in n.targets))
prefix = r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
typedef FILE *webs_t;
static int requested, present, unavailable;
static char observed[32];
static int mock_access(const char *path,int mode) {assert(!strcmp(path,"/proc/self/stat"));assert(mode==R_OK);return unavailable;}
static int pids(char *name) {assert(!strcmp(name,"stubby")||!strcmp(name,"https_dns_proxy"));return present;}
static int nvram_get_int(const char *key) {assert(!strcmp(key,"stubby_enable")||!strcmp(key,"doh_enable"));return requested;}
static int websWrite(webs_t wp,const char *format,...) {
 va_list args;int result;(void)wp;va_start(args,format);
 result=vsnprintf(observed,sizeof(observed),format,args);va_end(args);return result;
}
#define access mock_access
'''
suffix = r'''
static void check(char *service,int enabled,int process,int unknown,const char *expected) {
 char *args[]={service};requested=enabled;present=process;unavailable=unknown;
 ej_wr_dns_process_state(0,NULL,1,args);assert(!strcmp(observed,expected));
}
int main(void) {
 char *invalid[]={"untrusted-name"};char *names[]={"stubby","doh"};unsigned i;
 for(i=0;i<2;i++) {
  check(names[i],0,0,0,"0");check(names[i],1,1,0,"1");
  check(names[i],1,0,0,"2");check(names[i],0,1,0,"4");
  check(names[i],1,1,1,"3");check(names[i],0,0,1,"3");
 }
 ej_wr_dns_process_state(0,NULL,1,invalid);assert(!strcmp(observed,"3"));
 ej_wr_dns_process_state(0,NULL,0,NULL);assert(!strcmp(observed,"3"));
 puts("PASS DNS process observations; DNS/TLS functionality not inferred");return 0;
}
'''
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(prefix + code + suffix)
