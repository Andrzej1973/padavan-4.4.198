#!/usr/bin/env python3
"""Extract installed RC staging blocks; test their file/error behavior with injected failures."""
import argparse,re
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('source',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
s=(a.source/'trunk/user/rc/services_ex.c').read_text(encoding='utf-8')
s=s[s.index('int\nstart_dns_dhcpd(int is_ap_mode)'):s.index('\nvoid\nstop_dns_dhcpd(void)')]
def block(pattern):
 result=re.search(pattern,s,re.S)
 if not result:raise SystemExit('Installed staging source changed: '+pattern)
 return result.group(0).replace('/etc/','./')
early=block(r'#if defined\(BOARD_WR1200JS\)\n if\(nvram_get_int\("wr_iot_network_t"\).*?\n#endif')
opening=block(r'#if defined\(BOARD_WR1200JS\)\n if \(nvram_get_int\("wr_iot_network_t"\).*?\n\t\treturn errno;')
fragment=block(r'#if defined\(BOARD_WR1200JS\)\n \{\n  int result=wr_iot_dnsmasq.*?\n#endif')
closing=block(r'#if defined\(BOARD_WR1200JS\)\n if\(\*iot_candidate\) \{\n  int failed=ferror.*?\tfclose\(fp\);')
commit=block(r'#if defined\(BOARD_WR1200JS\)\n if\(\*iot_candidate\) \{\n  char option\[64\].*?\n#endif')
pre=r"""
#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <errno.h>
#include <assert.h>
#include <dirent.h>
#define BOARD_WR1200JS 1
static int gate=1,fault,parser_calls,close_calls,helper_calls,dhcp_calls;
static int nvram_get_int(const char *key){assert(!strcmp(key,"wr_iot_network_t"));return gate;}
static int wr_iot_dnsmasq(FILE *fp,int ap,const char *ip,const char *mask){(void)fp;(void)ap;(void)ip;(void)mask;dhcp_calls++;return fault==2||(fault==9&&dhcp_calls==2)?-1:1;}
static int injected_mkstemp(char *name){if(fault==1){errno=ENOSPC;return -1;}return mkstemp(name);}
static FILE *injected_tmpfile(void){if(fault==7){errno=EMFILE;return NULL;}return tmpfile();}
static int injected_fsync(int fd){if(fault==3){errno=EIO;return -1;}return fsync(fd);}
static int injected_fclose(FILE *fp){int result=fclose(fp);close_calls++;return (fault==4&&close_calls==2)||(fault==8&&close_calls==1)?EOF:result;}
static int injected_eval(const char *binary,const char *option,const char *config){assert(!strcmp(binary,"/usr/sbin/dnsmasq"));assert(!strcmp(option,"--test"));assert(!strncmp(config,"--conf-file=./dnsmasq.iot.",24));parser_calls++;return fault==5;}
static int injected_rename(const char *from,const char *to){if(fault==6){errno=EACCES;return -1;}return rename(from,to);}
#define tmpfile injected_tmpfile
#define mkstemp injected_mkstemp
#define fsync injected_fsync
#define fclose injected_fclose
#define rename injected_rename
#define eval injected_eval
static int installed_stage(void){
 FILE *fp;char iot_candidate[32]="";int is_ap_mode=0,is_dhcp_used=0;const char *ipaddr="192.168.1.1",*netmask="255.255.255.0";
"""
post=r"""
 (void)is_dhcp_used;return 0;
}
#undef tmpfile
#undef mkstemp
#undef fsync
#undef fclose
#undef rename
#undef eval
static void content(const char *expected){char text[64];FILE *fp=fopen("dnsmasq.conf","r");assert(fp);assert(fgets(text,sizeof(text),fp));assert(!strcmp(text,expected));assert(!fclose(fp));}
static void no_candidates(void){DIR *dir=opendir(".");struct dirent *entry;assert(dir);while((entry=readdir(dir)))assert(strncmp(entry->d_name,"dnsmasq.iot.",12));closedir(dir);}
int main(void){char directory[]="/tmp/iot-dnsmasq-stage-XXXXXX";int mode;assert(mkdtemp(directory));assert(!chdir(directory));
 for(mode=0;mode<=9;mode++){
  FILE *fp;fault=0;parser_calls=0;close_calls=0;helper_calls=0;dhcp_calls=0;fp=fopen("dnsmasq.conf","w");assert(fp);assert(fputs("old\n",fp)>=0);assert(!fclose(fp));fault=mode;
  if(mode){assert(installed_stage()!=0);content("old\n");}else{assert(!installed_stage());content("new\n");assert(parser_calls==1);}
  assert(helper_calls==((mode==2||mode==7||mode==8)?0:1));no_candidates();
 }
 fault=0;gate=0;parser_calls=0;assert(!installed_stage());content("new\n");assert(!parser_calls);no_candidates();
 assert(!unlink("dnsmasq.conf"));assert(!chdir("/tmp"));assert(!rmdir(directory));
 puts("PASS installed RC staging: candidate success; mkstemp/fragment/fsync/close/parser/rename failures retain previous config; no leftovers; legacy OFF path retained. Early invalid network/tmpfile/close failures stop before helper marker; parser result injected; real service rollback unverified.");return 0;
}
"""
a.output.write_text(pre+early+'\n helper_calls++;\n'+opening+'\n fputs("new\\n",fp);\n'+fragment+'\n'+closing+'\n'+commit+post,encoding='utf-8')
