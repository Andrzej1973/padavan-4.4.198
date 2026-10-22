/* Candidate dedicated CGI; excluded from production until RC transport and
 * observed activation/recovery are linked and verified. */
#include "http-request.h"
#include "control-record.h"
#include <time.h>
extern int wr_iot_http_is_post(void);
extern const char *wr_iot_http_content_type(void);
/* Must copy the request before returning, serialize ownership with RC and
 * return 1 only after published queue acceptance in volatile runtime storage.
 * Never return activation status
 * here. Implemented separately by control-client.c, never generic Apply. */
extern int wr_iot_rc_submit(const struct wr_iot_request *,char [33]);
extern int wr_iot_rc_status(const char *,struct wr_iot_control_result *);
#ifndef WR_IOT_HTTP_NOW
static unsigned long long wr_iot_http_monotonic(void){
 struct timespec ts;
 if(clock_gettime(CLOCK_MONOTONIC,&ts)||ts.tv_sec<=0)return 0;
 return (unsigned long long)ts.tv_sec;
}
#define WR_IOT_HTTP_NOW wr_iot_http_monotonic
#endif
static char wr_iot_http_csrf[33];
static char wr_iot_http_body[WR_IOT_HTTP_FORM_MAX];
static size_t wr_iot_http_length;

static void wr_iot_http_token_output(const char *url,FILE *stream)
{
 unsigned char random[16];size_t offset=0;ssize_t got;int fd,i;
 (void)url;
 if(!get_login_safe()){websWrite(stream,"{\"error\":\"unsafe_request\"}");return;}
 if(!wr_iot_http_csrf[0]){
  fd=open("/dev/urandom",O_RDONLY);
  if(fd<0){websWrite(stream,"{\"error\":\"unavailable\"}");return;}
  while(offset<sizeof(random)){
   got=read(fd,random+offset,sizeof(random)-offset);
   if(got<0&&errno==EINTR)continue;
   if(got<=0)break;
   offset+=(size_t)got;
  }
  close(fd);
  if(offset!=sizeof(random)){websWrite(stream,"{\"error\":\"unavailable\"}");return;}
  for(i=0;i<16;i++)snprintf(wr_iot_http_csrf+i*2,3,"%02x",random[i]);
 }
 websWrite(stream,"{\"token\":\"%s\"}",wr_iot_http_csrf);
}

static void wr_iot_http_apply_input(const char *url,FILE *stream,int length,char *boundary)
{
 (void)url;(void)boundary;
 memset(wr_iot_http_body,0,sizeof(wr_iot_http_body));wr_iot_http_length=0;
 if(length<=0||length>WR_IOT_HTTP_FORM_MAX)return;
 if(fread(wr_iot_http_body,1,(size_t)length,stream)!=(size_t)length){
  memset(wr_iot_http_body,0,sizeof(wr_iot_http_body));return;
 }
 wr_iot_http_length=(size_t)length;
}

static void wr_iot_http_apply_output(const char *url,FILE *stream)
{
 struct wr_iot_request request={0};char id[33]={0};size_t length;
 int accepted;
 (void)url;length=wr_iot_http_length;wr_iot_http_length=0;
 /* Live mode/ranges are deliberately revalidated by RC under its service
  * guard. Here validate the complete request structure and credentials only. */
 accepted=wr_iot_http_request_read(&request,get_login_safe(),
  wr_iot_http_is_post()?"POST":"GET",wr_iot_http_content_type(),
  wr_iot_http_csrf,wr_iot_http_body,length,1,1,0,NULL,0);
 memset(wr_iot_http_body,0,sizeof(wr_iot_http_body));
 if(!accepted){websWrite(stream,"{\"error\":\"invalid_request\"}");return;}
 accepted=wr_iot_rc_submit(&request,id);
 memset(&request,0,sizeof(request));
 if(accepted!=1||!memchr(id,0,sizeof(id))||!wr_iot_control_id(id)){
  websWrite(stream,"{\"error\":\"unavailable_or_busy\"}");return;
 }
 websWrite(stream,"{\"accepted\":true,\"id\":\"%s\"}",id);
}

static void wr_iot_http_result_output(const char *url,FILE *stream)
{
 struct wr_iot_control_result result={0};char id[33];const char *requested;
 unsigned long long now;
 (void)url;
 if(!get_login_safe()){websWrite(stream,"{\"error\":\"unsafe_request\"}");return;}
 requested=websGetVar(stream,"id","");
 if(!wr_iot_control_id(requested)){
  websWrite(stream,"{\"error\":\"invalid_request\"}");return;
 }
 memcpy(id,requested,33);now=WR_IOT_HTTP_NOW();
 if(!now||wr_iot_rc_status(id,&result)!=1||
    !wr_iot_control_result_current(&result,id,now,30)){
  websWrite(stream,"{\"id\":\"%s\",\"state\":\"unknown\"}",id);return;
 }
 websWrite(stream,"{\"id\":\"%s\",\"state\":\"%s\"}",id,wr_iot_control_state(result.state));
}
