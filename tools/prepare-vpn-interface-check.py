#!/usr/bin/env python3
"""Exercise emitted VPN interface observer with controlled sysfs data."""
import argparse
import ast
from pathlib import Path
p=argparse.ArgumentParser()
p.add_argument('--output',type=Path,required=True)
a=p.parse_args()
tree=ast.parse(Path(__file__).with_name('prepare-vpn-interface-status.py').read_text())
code=next(ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign)
          and any(isinstance(t,ast.Name) and t.id=='code' for t in n.targets))
prefix=r'''
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <unistd.h>
#include <errno.h>
typedef FILE *webs_t;
static int requested, unavailable, open_error;
static const char *input;
static char observed[32];
static FILE *mock_open(const char *path,const char *mode) {
 FILE *fp;assert(!strcmp(mode,"r"));
 assert(!strcmp(path,"/sys/class/net/wg0/flags")||!strcmp(path,"/sys/class/net/wg1/flags"));
 if(!input){errno=open_error;return NULL;}
 fp=tmpfile();assert(fp);assert(fputs(input,fp)>=0);rewind(fp);return fp;
}
static int mock_access(const char *path,int mode){assert(!strcmp(path,"/sys/class/net"));assert(mode==R_OK);return unavailable;}
static int nvram_get_int(const char *key){assert(!strcmp(key,"vpnc_enable")||!strcmp(key,"vpns_enable"));return requested;}
static int websWrite(webs_t wp,const char *format,...){va_list args;int n;(void)wp;va_start(args,format);n=vsnprintf(observed,sizeof(observed),format,args);va_end(args);return n;}
#define fopen mock_open
#define access mock_access
'''
suffix=r'''
static void check(char *role,int setting,const char *data,int error,const char *expected){
 char *args[]={role};requested=setting;input=data;open_error=error;
 ej_wr_vpn_interface_state(0,NULL,1,args);assert(!strcmp(observed,expected));
}
int main(void){
 char *roles[]={"client","server"};char *invalid[]={"unknown"};unsigned i;
 for(i=0;i<2;i++){
  check(roles[i],0,NULL,ENOENT,"0");check(roles[i],1,NULL,ENOENT,"2");
  check(roles[i],1,"0x1\n",0,"1");check(roles[i],0,"0x1\n",0,"4");
  check(roles[i],1,"0x0\n",0,"5");check(roles[i],1,NULL,EACCES,"3");
  check(roles[i],1,"invalid\n",0,"3");check(roles[i],1,"0x1 extra\n",0,"3");
  unavailable=1;check(roles[i],1,"0x1\n",0,"3");unavailable=0;
 }
 ej_wr_vpn_interface_state(0,NULL,0,NULL);assert(!strcmp(observed,"3"));
 ej_wr_vpn_interface_state(0,NULL,1,invalid);assert(!strcmp(observed,"3"));
 puts("PASS VPN interface observation; handshake and routes not inferred");return 0;
}
'''
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(prefix+code+suffix)
