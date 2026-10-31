#!/usr/bin/env python3
"""Generate a fixture for the actual USBIP settings HTTP and file-store code."""
import argparse
import json
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--output',type=Path,required=True)
a=p.parse_args();here=Path(__file__).parent
prefix=r'''
#include <assert.h>
#include <errno.h>
#include <ctype.h>
#include <limits.h>
#include <stdarg.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
static int fail_directory_fsync;
static int wr_usbip_test_fsync(int fd){
 struct stat s;
 if(fail_directory_fsync&&fstat(fd,&s)==0&&S_ISDIR(s.st_mode)){errno=EIO;return -1;}
 return fsync(fd);
}
#define WR_USBIP_FSYNC(fd) wr_usbip_test_fsync(fd)
static char settings_dir[PATH_MAX],settings_lock[PATH_MAX];
#define WR_USBIP_EXPORT_DIRECTORY settings_dir
#define WR_USBIP_LIFECYCLE_LOCK settings_lock
typedef FILE *webs_t;
static int safe,post=1,parsed;
static char wr_usbip_csrf[33]="0123456789abcdef0123456789abcdef";
static char token[40]="0123456789abcdef0123456789abcdef",ack[4]="1",table[18432],reply[20000];
static int get_login_safe(void){return safe;}
static int wr_usbip_request_is_post(void){return post;}
static int websWrite(webs_t wp,const char *fmt,...){
 va_list ap;int n;size_t remaining=sizeof(reply)-strlen(reply);(void)wp;
 va_start(ap,fmt);n=vsnprintf(reply+strlen(reply),remaining,fmt,ap);va_end(ap);
 assert(n>=0&&(size_t)n<remaining);return n;
}
static char *websGetVar(webs_t wp,const char *name,const char *fallback){
 (void)wp;if(!strcmp(name,"token"))return token;if(!strcmp(name,"ack"))return ack;
 if(!strcmp(name,"table_hex"))return table;
 return (char *)fallback;
}
static void init_cgi(char *body){if(body)parsed++;}
'''
tests=r'''
static void submit(void){reply[0]=0;wr_usbip_settings_post=1;wr_usbip_settings_output("",NULL);}
static void input(const char *body,size_t n){FILE *f=tmpfile();assert(f);assert(fwrite(body,1,n,f)==n);rewind(f);wr_usbip_settings_input("",f,(int)n,NULL);fclose(f);}
int main(void){
 char root[]="/tmp/wr-usbip-http-settings-XXXXXX",text[WR_USBIP_EXPORT_TEXT_MAX],path[PATH_MAX];
 struct wr_usbip_export_rule rules[16]={0},loaded[16];size_t i;
 assert(mkdtemp(root));snprintf(settings_dir,sizeof(settings_dir),"%s/storage",root);
 snprintf(settings_lock,sizeof(settings_lock),"%s/lock",root);
 submit();assert(strstr(reply,"unsafe_request")&&access(settings_dir,F_OK));safe=1;
 post=0;submit();assert(strstr(reply,"unsafe_request"));post=1;
 token[0]='x';submit();assert(strstr(reply,"invalid_token"));token[0]='0';
 ack[0]='0';submit();assert(strstr(reply,"confirmation"));ack[0]='1';
 strcpy(table,"zz");submit();assert(strstr(reply,"invalid_or_unavailable")&&access(settings_dir,F_OK));
 assert(wr_usbip_export_encode(rules,text,sizeof(text)));
 for(i=0;text[i];i++)snprintf(table+i*2,3,"%02x",(unsigned char)text[i]);
 parsed=0;input("a=%",3);assert(!wr_usbip_settings_post&&parsed==0);
 input("a=%00",5);assert(!wr_usbip_settings_post&&parsed==0);
 input("a=%GG",5);assert(!wr_usbip_settings_post&&parsed==0);
 {char *big=malloc(32769);assert(big);memset(big,'a',32769);input(big,32769);free(big);assert(!wr_usbip_settings_post&&parsed==0);}
 {char nul[2]={'x',0};input(nul,2);assert(!wr_usbip_settings_post&&parsed==0);}
 input("a=b",3);assert(wr_usbip_settings_post&&parsed==1);
 reply[0]=0;wr_usbip_settings_output("",NULL);
 assert(strstr(reply,"\"saved\":true")&&strstr(reply,"\"applied\":false")&&strstr(reply,"\"flash_committed\":false"));
 assert(wr_usbip_settings_read(loaded)==WR_USBIP_SETTINGS_READY);
 assert(!memcmp(loaded,rules,sizeof(rules)));
 rules[0].enabled=1;strcpy(rules[0].bus,"1-1");strcpy(rules[0].vendor,"1234");
 strcpy(rules[0].product,"beef");strcpy(rules[0].serial_hex,"756e6974");
 assert(wr_usbip_export_encode(rules,text,sizeof(text)));
 for(i=0;text[i];i++)snprintf(table+i*2,3,"%02x",(unsigned char)text[i]);
 fail_directory_fsync=1;submit();fail_directory_fsync=0;
 assert(strstr(reply,"\"saved\":true")&&strstr(reply,"\"synchronized\":false"));
 assert(strstr(reply,"\"applied\":false")&&strstr(reply,"\"flash_committed\":false"));
 assert(wr_usbip_settings_read(loaded)==WR_USBIP_SETTINGS_READY);
 assert(!memcmp(loaded,rules,sizeof(rules)));
 reply[0]=0;wr_usbip_settings_output("",NULL);assert(strstr(reply,"unsafe_request"));
 reply[0]=0;ej_wr_usbip_export_settings(0,NULL,0,NULL);assert(strstr(reply,"\"state\":1")&&strstr(reply,table));
 safe=0;reply[0]=0;ej_wr_usbip_export_settings(0,NULL,0,NULL);assert(strstr(reply,"unsafe_request"));
 assert(snprintf(path,sizeof(path),"%s/exports.v1",settings_dir)<(int)sizeof(path));
 assert(unlink(path)==0&&rmdir(settings_dir)==0&&unlink(settings_lock)==0&&rmdir(root)==0);
 puts("PASS USBIP HTTP settings: authentication, body validation, save-only behavior, directory-fsync uncertainty and private roundtrip");return 0;
}
'''
code=(here/'http-settings.inc').read_text(encoding='utf-8').replace(
    '#include "wr-usbip/export-settings.h"', '#include '+json.dumps(str((here/'export-settings.h').resolve())))
a.output.parent.mkdir(parents=True,exist_ok=True)
a.output.write_text(prefix+code+tests,encoding='utf-8',newline='\n')
