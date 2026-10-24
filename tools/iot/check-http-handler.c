#include <assert.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
static int safe=1,post=1,calls,submit_result=1;
static const char *mime="application/x-www-form-urlencoded";
static char reply[256];
static const char *requested_id="0123456789abcdef0123456789abcdef";
static int status_calls,status_available=1;
static unsigned long long result_observed=145;
static int result_state=3;
static const char *websGetVar(FILE *stream,const char *key,const char *fallback){
 (void)stream;assert(!strcmp(key,"id"));return requested_id?requested_id:fallback;
}
static unsigned long long test_now(void){return 150;}
#define WR_IOT_HTTP_NOW test_now
static int get_login_safe(void){return safe;}
static int websWrite(FILE *stream,const char *format,...){
 int n;va_list args;(void)stream;va_start(args,format);
 n=vsnprintf(reply,sizeof(reply),format,args);va_end(args);return n;
}
#include "http-handler.inc"
int wr_iot_http_is_post(void){return post;}
const char *wr_iot_http_content_type(void){return mime;}
int wr_iot_rc_submit(const struct wr_iot_request *request,char id[33]){
 assert(request->enabled&&!strcmp(request->ssid,"IoT")&&
        !strcmp(request->password,"password123"));
 calls++;strcpy(id,"0123456789abcdef0123456789abcdef");return submit_result;
}
int wr_iot_rc_status(const char *id,struct wr_iot_control_result *result){
 status_calls++;strcpy(result->id,id);result->created=140;
 result->observed=result_observed;result->state=(enum wr_iot_result_state)result_state;
 return status_available;
}
static void input(const char *body,int announced){
 FILE *fp=tmpfile();assert(fp);
 assert(fwrite(body,1,strlen(body),fp)==strlen(body));rewind(fp);
 wr_iot_http_apply_input("wr_iot_apply.cgi",fp,announced,NULL);
 assert(!fclose(fp));
}
static void output(void){
 wr_iot_http_apply_output("wr_iot_apply.cgi",NULL);
 assert(!wr_iot_http_length&&!wr_iot_http_body[0]);
}
int main(void){
 const char *body="wr_iot_request_enable=1&wr_iot_request_ssid=IoT"
  "&wr_iot_request_psk=password123&wr_iot_request_gateway=192.168.50.1"
  "&wr_iot_request_mask=255.255.255.0&wr_iot_request_start=192.168.50.20"
  "&wr_iot_request_end=192.168.50.200&token=0123456789abcdef0123456789abcdef";
 strcpy(wr_iot_http_csrf,"0123456789abcdef0123456789abcdef");
 wr_iot_http_token_output("wr_iot_token.cgi",NULL);assert(strstr(reply,"\"token\""));
 input(body,(int)strlen(body));output();assert(calls==1&&strstr(reply,"\"accepted\":true"));
 assert(!strstr(reply,"password")&&!strstr(reply,"applied"));
 /* Consumed POST bodies cannot be replayed through a subsequent output. */
 output();assert(calls==1&&strstr(reply,"invalid_request"));
 safe=0;input(body,(int)strlen(body));output();assert(calls==1);
 wr_iot_http_token_output("wr_iot_token.cgi",NULL);assert(strstr(reply,"unsafe_request"));safe=1;
 post=0;input(body,(int)strlen(body));output();assert(calls==1);post=1;
 mime=NULL;input(body,(int)strlen(body));output();assert(calls==1);
 mime="application/json";input(body,(int)strlen(body));output();assert(calls==1);
 mime="application/x-www-form-urlencoded";
 wr_iot_http_csrf[0]='f';input(body,(int)strlen(body));output();assert(calls==1);
 wr_iot_http_csrf[0]='0';
 input(body,(int)strlen(body)+1);output();assert(calls==1);
 input(body,WR_IOT_HTTP_FORM_MAX+1);output();assert(calls==1);
 submit_result=0;input(body,(int)strlen(body));output();assert(calls==2&&strstr(reply,"unavailable_or_busy"));
 wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(status_calls==1&&strstr(reply,"\"applied\""));
 result_state=WR_IOT_RESULT_QUEUED;
 wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(strstr(reply,"\"queued\"")&&!strstr(reply,"\"applied\""));
 result_state=WR_IOT_RESULT_RECOVERY;
 wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(strstr(reply,"recovery_required"));
 result_state=WR_IOT_RESULT_APPLIED;result_observed=110;
 wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(strstr(reply,"unknown"));
 result_observed=160;
 wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(strstr(reply,"unknown"));
 status_available=0;wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(strstr(reply,"unknown"));
 {int before=status_calls;
 requested_id="bad";wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(status_calls==before&&strstr(reply,"invalid_request"));
 safe=0;wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(status_calls==before&&strstr(reply,"unsafe_request"));}
 puts("PASS IoT CGI candidate: guarded POST, one-shot body, queue acceptance distinct from fresh ID-bound observed result");
 return 0;
}
