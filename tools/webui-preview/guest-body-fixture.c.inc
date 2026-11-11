#define _GNU_SOURCE
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "wr-shared-wifi/modern-body.h"
#define MIN(a,b) ((int)(a)<(int)(b)?(int)(a):(int)(b))
static char post_buf[65535];static int group_del_map[1],rejected;
static int wr_modern_guest_post_allowed(void){return 1;}
static void wr_modern_guest_input_fail(void){rejected=1;}
static void websScan(const char *body){(void)body;abort();}
/* ACTUAL_CGI */
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
/* ACTUAL_INPUT */
#pragma GCC diagnostic pop
/* ACTUAL_CLEAR */
static void body(const char *text,size_t available,int declared)
{
 FILE *stream=tmpfile();assert(stream);assert(fwrite(text,1,available,stream)==available);rewind(stream);rejected=0;
 do_html_apply_post("start_apply.htm",stream,declared,NULL);fclose(stream);
}
static void empty(void)
{
 assert(!get_cgi("wr_modern_guest_version"));
 for(size_t i=0;i<sizeof(post_buf);i++)assert(post_buf[i]==0);
}
int main(void)
{
 const char *valid="wr_modern_guest_version=1&rt_guest_ssid=My+Guest%26%3B%3D%25";
 body(valid,strlen(valid),(int)strlen(valid));assert(!rejected);
 assert(!strcmp(get_cgi("rt_guest_ssid"),"My Guest&;=%"));
 wr_modern_body_clear();empty();
 const char *unicode="wr_modern_guest_version=1&rt_guest_ssid=%D0%94%D1%96%D0%BC";
 body(unicode,strlen(unicode),(int)strlen(unicode));assert(!rejected&&!strcmp(get_cgi("rt_guest_ssid"),"Дім"));wr_modern_body_clear();empty();
 const char *bad[]={"wr_modern_guest_version=1&rt_guest_ssid=A&r%74_guest_ssid=B","wr_modern_guest_version=1&x=%","wr_modern_guest_version=1&x=%GG","wr_modern_guest_version=1&x=%00","wr_modern_guest_version=1&x","wr_modern_guest_version=1&wr_modern_wifi_version=1"};
 for(unsigned int i=0;i<sizeof(bad)/sizeof(bad[0]);i++){
  body(bad[i],strlen(bad[i]),(int)strlen(bad[i]));assert(rejected);empty();
 }
 body(valid,strlen(valid),(int)strlen(valid)+3);assert(rejected);empty();
 body(valid,strlen(valid),0);assert(rejected);empty();
 body(valid,strlen(valid),8193);assert(rejected);empty();
 char nul[]="wr_modern_guest_version=1&x=ab\0cd";
 body(nul,sizeof(nul)-1,(int)sizeof(nul)-1);assert(rejected);empty();
 // Valid Classic decoder behavior is preserved by candidate memmove correction.
 char legacy[]="a=one%20two;b=last";init_cgi(legacy);
 assert(!strcmp(get_cgi("a"),"one two")&&!strcmp(get_cgi("b"),"last"));init_cgi(NULL);
 assert(wr_modern_content_length(" 8192\r\n"));assert(wr_modern_content_length("1"));
 const char *lengths[]={NULL,"","0","0100","0x10","-1","+1","8193","10000","1x"};
 for(unsigned int i=0;i<sizeof(lengths)/sizeof(lengths[0]);i++)assert(!wr_modern_content_length(lengths[i]));
 puts("PASS actual marked POST input + CGI: exact body, short/oversize/NUL/alias duplicates/malformed escapes reject before CGI, decoded values and clear; Classic valid decode retained; host only");return 0;
}
