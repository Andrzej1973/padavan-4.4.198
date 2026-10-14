#!/usr/bin/env python3
"""Execute the emitted endpoint with deterministic proc/sysfs failures in CI."""
import argparse
import ast
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
tree = ast.parse(Path(__file__).with_name('prepare-usbip-status.py').read_text(encoding='utf-8'))
endpoint = next(ast.literal_eval(n.value) for n in tree.body
                if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'endpoint' for t in n.targets))
harness = r'''
#include <assert.h>
#include <errno.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
typedef void *webs_t;
static int root_error, root_file, root_denied, module_error, module_file, proc_denied, running;
static char reply[256];
static int fake_stat(const char *path, struct stat *st) {
 memset(st,0,sizeof(*st));
 if(!strcmp(path,"/sys/module")) {
  if(root_error){errno=root_error;return -1;}
  st->st_mode=root_file?S_IFREG:S_IFDIR;return 0;
 }
 if(module_error){errno=module_error;return -1;}
 st->st_mode=module_file?S_IFREG:S_IFDIR;return 0;
}
static int fake_access(const char *path,int mode) {
 (void)mode;
 if((!strcmp(path,"/sys/module") && root_denied) ||
    (!strcmp(path,"/proc/self/stat") && proc_denied)){errno=EACCES;return -1;}
 return 0;
}
static int pids(char *name){assert(!strcmp(name,"usbipd"));return running;}
static int websWrite(webs_t wp,const char *format,...) {
 va_list ap;int n;(void)wp;va_start(ap,format);n=vsnprintf(reply,sizeof(reply),format,ap);va_end(ap);return n;
}
#define stat fake_stat
#define access fake_access
'''
# Keep the struct tag intact while replacing calls in the emitted source.
endpoint = endpoint.replace('stat(', 'fake_stat(').replace('access(', 'fake_access(')
harness = harness.replace('#define stat fake_stat\n#define access fake_access\n','')
tests = r'''
static void expect(const char *json) {
 ej_wr_usbip_state(0,NULL,0,NULL);assert(!strcmp(reply,json));
}
int main(void) {
 expect("{\"core\":1,\"host\":1,\"vhci\":1,\"daemon\":0}");
 running=1;expect("{\"core\":1,\"host\":1,\"vhci\":1,\"daemon\":1}");
 module_file=1;expect("{\"core\":2,\"host\":2,\"vhci\":2,\"daemon\":1}");
 module_file=0;
 module_error=ENOENT;expect("{\"core\":0,\"host\":0,\"vhci\":0,\"daemon\":1}");
 module_error=EACCES;expect("{\"core\":2,\"host\":2,\"vhci\":2,\"daemon\":1}");
 module_error=ENOENT;root_error=ENOENT;
 expect("{\"core\":2,\"host\":2,\"vhci\":2,\"daemon\":1}");
 root_error=0;root_file=1;
 expect("{\"core\":2,\"host\":2,\"vhci\":2,\"daemon\":1}");
 root_file=0;root_denied=1;proc_denied=1;
 expect("{\"core\":2,\"host\":2,\"vhci\":2,\"daemon\":2}");
 ej_wr_usbip_state(0,NULL,1,NULL);assert(!strcmp(reply,"{\"error\":\"invalid_request\"}"));
 puts("PASS emitted USB/IP endpoint: module absence, source failures, process states and invalid arguments");return 0;
}
'''
a.output.parent.mkdir(parents=True, exist_ok=True)
a.output.write_text(harness + endpoint + tests, encoding='utf-8')
