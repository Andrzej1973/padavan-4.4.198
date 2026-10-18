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
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include "wr-doh-instances.h"
typedef FILE *webs_t;
static int requested, present, unavailable;
static char observed[256];
static unsigned configured_mask;
static struct wr_doh_instances slots;
static const char *nvram_safe_get(const char *key){unsigned index;assert(sscanf(key,"doh_server%u",&index)==1&&index<4);return configured_mask&(1U<<index)?"private-resolver-url":"";}
static struct wr_doh_instances mock_doh_observe(unsigned configured,const char *pids_root,const char *proc_root){assert(configured==configured_mask);assert(!strcmp(pids_root,"/var/run/doh-proxy")&&!strcmp(proc_root,"/proc"));slots.configured=configured;return slots;}
#define wr_doh_observe mock_doh_observe
static int mock_access(const char *path,int mode) {assert(!strcmp(path,"/proc/self/stat"));assert(mode==R_OK);return unavailable;}
static int wr_process_present(const char *name) {assert(!strcmp(name,"stubby")||!strcmp(name,"https_dns_proxy"));return present;}
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
  check(names[i],1,-1,0,"3");check(names[i],0,-1,0,"3");
 }
 ej_wr_dns_process_state(0,NULL,1,invalid);assert(!strcmp(observed,"3"));
 ej_wr_dns_process_state(0,NULL,0,NULL);assert(!strcmp(observed,"3"));
 configured_mask=5;requested=1;present=1;unavailable=0;slots.owned=1;
 ej_wr_doh_instance_state(0,NULL,0,NULL);
 assert(!strcmp(observed,"{\"state\":1,\"requested\":1,\"configuredMask\":5,\"ownedMask\":1,\"unknownMask\":0,\"duplicateMask\":0}"));
 requested=0;slots.owned=5;slots.unknown=2;slots.duplicate=2;
 ej_wr_doh_instance_state(0,NULL,0,NULL);assert(strstr(observed,"\"state\":4")&&strstr(observed,"\"unknownMask\":2")&&strstr(observed,"\"duplicateMask\":2"));
 present=-1;ej_wr_doh_instance_state(0,NULL,0,NULL);assert(strstr(observed,"\"state\":3"));
 present=1;
 unavailable=1;ej_wr_doh_instance_state(0,NULL,0,NULL);assert(strstr(observed,"\"state\":3")&&strstr(observed,"\"unknownMask\":15")&&strstr(observed,"\"ownedMask\":0"));
 ej_wr_doh_instance_state(0,NULL,1,invalid);assert(!strcmp(observed,"{\"error\":\"invalid_request\"}"));
 puts("PASS DNS process observations; DNS/TLS functionality not inferred");return 0;
}
'''
a.output.parent.mkdir(parents=True, exist_ok=True)
(a.output.parent/'wr-doh-instances.h').write_bytes(Path(__file__).with_name('doh-instance-status.h').read_bytes())
a.output.write_text(prefix + code + suffix)
