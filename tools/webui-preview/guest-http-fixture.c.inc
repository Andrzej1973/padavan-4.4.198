#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <strings.h>
#include <time.h>
#include <sys/stat.h>
#include "wr-shared-wifi/guest-transport.h"
typedef int uaddr;
typedef struct {int fd,usa;} conn_item_t;
#define HTTP_METHOD_GET 0
#define HTTP_METHOD_POST 1
#define HTTP_METHOD_HEAD 2
static int http_has_lang,login_fixture=3,status_code,inputs,outputs,observed,auth_calls;
static int wr_modern_guest_post_authorized;
int wr_modern_guest_post_allowed(void){return wr_modern_guest_post_authorized;}
static int set_preferred_lang(const char *v){(void)v;return 1;}
static time_t tdate_parse(const char *v){(void)v;return 0;}
static void send_headers(int status,const char *title,const char *extra,const char *mime,struct stat *st,FILE *stream){(void)title;(void)extra;(void)mime;(void)st;(void)stream;status_code=status;}
static void send_error(int status,const char *title,const char *extra,const char *message,FILE *stream){(void)message;send_headers(status,title,extra,NULL,NULL,stream);}
static void usockaddr_to_uaddr(const int *from,uaddr *to){*to=*from;}
static int http_login_check(const uaddr *ip){(void)ip;return login_fixture;}
static int auth_check(const char *value){auth_calls++;return value&&strstr(value,"Basic fixture-good");}
static void http_login(const uaddr *ip){(void)ip;}
static void http_logout(const uaddr *ip){(void)ip;}
static void send_authenticate(FILE *stream){send_error(401,"Unauthorized",NULL,"auth",stream);}
static void eat_post_data(FILE *stream,int length){while(length-->0)assert(fgetc(stream)!=EOF);}
static void try_pull_data(FILE *stream,int fd){(void)stream;(void)fd;}
static void do_uncgi_query(char *query){(void)query;}
static void do_cgi_clear(void){}
static void do_file(const char *file,FILE *stream){(void)file;(void)stream;}
static void do_ej(const char *file,FILE *stream){(void)file;(void)stream;outputs++;observed=wr_modern_guest_post_allowed();}
static void input(const char *file,FILE *stream,int length,char *boundary){(void)file;(void)boundary;inputs++;eat_post_data(stream,length);}
struct mime_handler {const char *pattern,*mime_type,*extra_header;void (*input)(const char *,FILE *,int,char *);void (*output)(const char *,FILE *);int need_auth;};
static struct mime_handler mime_handlers[]={
 {"start_apply.htm","text/html",NULL,input,do_ej,1},
 {"other.htm","text/html",NULL,input,do_ej,1},
 {"Nologin.asp","text/html",NULL,NULL,do_ej,0},
 {NULL,NULL,NULL,NULL,NULL,0}};
static int match(const char *pattern,const char *file){return !strcmp(pattern,file);}
/* ACTUAL_HANDLE_REQUEST */
static void request(const char *method,const char *path,const char *headers,int auth,int login)
{
 FILE *stream=tmpfile();conn_item_t item={0};assert(stream);
 fprintf(stream,"%s %s HTTP/1.1\r\nHost: fixture\r\nContent-Length: 0\r\n%s%s\r\n",method,path,auth?"Authorization: Basic fixture-good\r\n":"",headers);rewind(stream);
 inputs=outputs=auth_calls=observed=status_code=0;login_fixture=login;
 handle_request(stream,&item);fclose(stream);
}
int main(void)
{
 request("POST","/start_apply.htm","X-WR-Modern: 1\r\n",1,3);assert(inputs==1&&outputs==1&&observed&&auth_calls==1);
 request("GET","/start_apply.htm","X-WR-Modern: 1\r\n",1,3);assert(!inputs&&outputs==1&&!observed);
 request("HEAD","/start_apply.htm","X-WR-Modern: 1\r\n",1,3);assert(!inputs&&!outputs&&!wr_modern_guest_post_allowed());
 request("OPTIONS","/start_apply.htm","Access-Control-Request-Headers: X-WR-Modern\r\n",0,3);assert(status_code==501&&!inputs&&!outputs);
 request("POST","/start_apply.htm","X-WR-Modern: 1\r\nX-WR-Modern: 1\r\n",1,3);assert(inputs==1&&outputs==1&&!observed);
 request("POST","/start_apply.htm","",1,3);assert(inputs==1&&outputs==1&&!observed);
 request("POST","/start_apply.htm?injected=1","X-WR-Modern: 1\r\n",1,3);assert(inputs==1&&outputs==1&&!observed);
 request("POST","/other.htm","X-WR-Modern: 1\r\n",1,3);assert(inputs==1&&outputs==1&&!observed);
 request("POST","/start_apply.htm","X-WR-Modern: 1\r\n",0,3);assert(status_code==401&&!inputs&&!outputs);
 request("POST","/start_apply.htm","X-WR-Modern: 1\r\n",0,1);assert(status_code==401&&!inputs&&!outputs&&auth_calls==1);
 request("POST","/start_apply.htm","X-WR-Modern: 1\r\n",1,1);assert(inputs==1&&outputs==1&&observed&&auth_calls==1);
 request("POST","/start_apply.htm","",0,1);assert(inputs==1&&outputs==1&&!observed&&!auth_calls); /* Classic exception preserved. */
 request("POST","/start_apply.htm","X-WR-Modern: 1\r\n",0,0);assert(outputs==1&&!observed&&!auth_calls); /* redirected Nologin */
 puts("PASS actual HTTP handle_request: POST/header/route/query, duplicates, reset, OPTIONS501, authentication ordering incl trusted-local Guest; auth/body/output fixtures, not browser/runtime");return 0;
}
