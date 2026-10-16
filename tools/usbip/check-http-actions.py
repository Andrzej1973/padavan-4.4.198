#!/usr/bin/env python3
"""Generate native tests of HTTP guards with a mocked job scheduler."""
import argparse
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
prefix=r'''
#include <assert.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <sys/types.h>
#include <unistd.h>
typedef FILE *webs_t;
struct wr_usbip_job_result {char id[33];unsigned state;unsigned long long started,observed;int code;};
static int safe,post,reaped=1,started=1,readable=1,calls,parsed;
static char reply[512],request_token[40],operation[20]="bind",ack[4]="1";
static char request_serial[514]="756e6974";
int wr_usbip_request_is_post(void){return post;}
static int get_login_safe(void){return safe;}
static int websWrite(webs_t wp,const char *format,...) {
 va_list ap;int n;(void)wp;va_start(ap,format);n=vsnprintf(reply,sizeof(reply),format,ap);va_end(ap);return n;
}
static char *websGetVar(webs_t wp,const char *key,const char *fallback){
 (void)wp;
 if(!strcmp(key,"token"))return request_token;
 if(!strcmp(key,"ack"))return ack;
 if(!strcmp(key,"operation"))return operation;
 if(!strcmp(key,"busid"))return "1-1";
 if(!strcmp(key,"vendor"))return "1234";
 if(!strcmp(key,"product"))return "abcd";
 if(!strcmp(key,"serial_hex"))return request_serial;
 return (char *)fallback;
}
static void init_cgi(char *p){(void)p;}
static void do_html_apply_post(const char *u,FILE *f,int c,char *b){(void)u;(void)f;(void)c;(void)b;parsed++;}
static int wr_usbip_job_reap(pid_t *p){(void)p;return reaped;}
static int wr_usbip_job_args(const char *a,const char *b,const char *v,const char *p){
 return !strcmp(a,"bind")&&!strcmp(b,"1-1")&&!strcmp(v,"1234")&&!strcmp(p,"abcd");
}
static int wr_usbip_job_start_serial(const char *d,const char *a,const char *b,const char *v,const char *p,const char *serial,char *id,pid_t *pid){
 (void)d;(void)a;(void)b;(void)v;(void)p;assert(!strcmp(serial,"756e6974"));calls++;strcpy(id,"0123456789abcdef0123456789abcdef");*pid=123;return started;
}
static unsigned long long wr_usbip_job_now(void){return 100;}
static int wr_usbip_job_read(const char *d,const char *id,unsigned long long n,unsigned long long age,struct wr_usbip_job_result *out){
 (void)d;(void)n;assert(age==120);memset(out,0,sizeof(*out));strcpy(out->id,id);out->state=2;return readable;
}
'''
tests=r'''
static void submit(void){wr_usbip_post_seen=1;wr_usbip_action_output("",NULL);}
int main(void){
 char *args[]={"0123456789abcdef0123456789abcdef"};FILE *fp;
 ej_wr_usbip_token(0,NULL,0,NULL);assert(!strcmp(reply,"\"\""));
 safe=1;ej_wr_usbip_token(0,NULL,0,NULL);assert(strlen(wr_usbip_csrf)==32);
 strcpy(request_token,wr_usbip_csrf);
 submit();assert(strstr(reply,"unsafe_request")&&calls==0);post=1;
 strcpy(request_token,"bad");submit();assert(strstr(reply,"invalid_token")&&calls==0);
 strcpy(request_token,wr_usbip_csrf);ack[0]=0;submit();assert(strstr(reply,"confirmation")&&calls==0);strcpy(ack,"1");
 strcpy(operation,"invalid");submit();assert(strstr(reply,"invalid_request")&&calls==0);strcpy(operation,"bind");
 strcpy(request_serial,"f");submit();assert(strstr(reply,"invalid_request")&&calls==0);
 strcpy(request_serial,"GG");submit();assert(strstr(reply,"invalid_request")&&calls==0);
 memset(request_serial,'a',513);request_serial[513]=0;submit();assert(strstr(reply,"invalid_request")&&calls==0);
 strcpy(request_serial,"756e6974");
 reaped=0;submit();assert(strstr(reply,"busy")&&calls==0);reaped=1;
 started=0;submit();assert(strstr(reply,"unavailable")&&calls==1);started=1;
 submit();assert(strstr(reply,"\"accepted\":true")&&calls==2);
 wr_usbip_action_output("",NULL);assert(strstr(reply,"unsafe_request")&&calls==2);
 ej_wr_usbip_job_state(0,NULL,1,args);assert(strstr(reply,"\"state\":2"));
 readable=0;ej_wr_usbip_job_state(0,NULL,1,args);assert(strstr(reply,"unknown_result"));
 safe=0;ej_wr_usbip_job_state(0,NULL,1,args);assert(strstr(reply,"unsafe_request"));
 fp=tmpfile();assert(fp);wr_usbip_action_input("",fp,1025,NULL);assert(!wr_usbip_post_seen&&parsed==0);
 wr_usbip_action_input("",fp,1,NULL);assert(wr_usbip_post_seen&&parsed==1);fclose(fp);
 puts("PASS USB/IP HTTP action: POST, safe session, CSRF, confirmation, args, busy, result, body bound");return 0;
}
'''
code=Path(__file__).with_name('http-actions.inc').read_text().replace('#include "wr-usbip-job.h"','')
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(prefix+code+tests)
