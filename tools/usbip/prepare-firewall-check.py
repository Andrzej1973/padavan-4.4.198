#!/usr/bin/env python3
"""Extract the real rule emitter for a native, side-effect-free CI test."""
import argparse
import ast
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
tree=ast.parse(Path(__file__).with_name('prepare-firewall.py').read_text())
helper=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
            and any(isinstance(t,ast.Name) and t.id=='helper' for t in n.targets))
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(r'''
#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
''' +helper+r'''
int main(void) {
 const char *bad[]={NULL,"","lo","br0\n-A INPUT -j ACCEPT","br+","abcdefghijklmnop"};
 size_t i;
 for(i=0;i<sizeof(bad)/sizeof(bad[0]);i++) {
  char *out=NULL;size_t length=0;FILE *fp=open_memstream(&out,&length);assert(fp);
  wr_usbip_filter_input(fp,bad[i]);assert(!fclose(fp));
  assert(!strcmp(out,"-A INPUT -p tcp --dport 3240 -j WRUSBIP_BASE\n-A WRUSBIP_BASE -i lo -j RETURN\n-A WRUSBIP_BASE -j DROP\n"));free(out);
 }
 {char *out=NULL;size_t n=0;FILE *fp=open_memstream(&out,&n);assert(fp);
 wr_usbip_filter_input(fp,"br0");assert(!fclose(fp));
 assert(!strcmp(out,"-A INPUT -p tcp --dport 3240 -j WRUSBIP_BASE\n-A WRUSBIP_BASE -i lo -j RETURN\n-A WRUSBIP_BASE -i br0 -j RETURN\n-A WRUSBIP_BASE -j DROP\n"));free(out);}
 puts("PASS USB/IP atomic firewall emitter: LAN/loopback policy, invalid interfaces and fail-closed output");return 0;
}
''')
