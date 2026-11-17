#include <assert.h>
#include <stdio.h>
#include <stdarg.h>
#include <string.h>
#include <errno.h>
#include <fcntl.h>
#include <unistd.h>
static int safe=1,post=1,calls,config_calls,save_calls,save_mode,submit_result=1;
static const char *mime="application/x-www-form-urlencoded";
static char reply[1024];
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
static int edit_calls;static enum wr_iot_config_edit_mode edit_mode;
int wr_iot_rc_submit_edit(const struct wr_iot_saved_config *fields,const char *revision,
 enum wr_iot_config_edit_mode mode,enum wr_iot_config_key_action action,char id[33]){
 assert(!strcmp(fields->profile.ssid,"IoT")&&!fields->profile.password[0]&&action==WR_IOT_CONFIG_KEY_KEEP);
 assert(!strcmp(revision,"ffffffffffffffffffffffffffffffff"));edit_calls++;edit_mode=mode;
 strcpy(id,"0123456789abcdef0123456789abcdef");return submit_result;
}
static int view_calls,view_reply=1;
int wr_iot_http_view_read(struct wr_iot_config_view *view,char revision[33]){
 view_calls++;memset(view,0,sizeof(*view));memset(revision,'f',32);revision[32]=0;
 if(view_reply==2)return 1;
 view->key_present=1;view->enabled=0;strcpy(view->ssid,"IoT \"</script>&\\");
 strcpy(view->gateway,"192.168.50.1");strcpy(view->mask,"255.255.255.0");
 strcpy(view->first,"192.168.50.20");strcpy(view->last,"192.168.50.200");
 if(view_reply==3)view->ssid[24]='x';
 return view_reply==0?0:1;
}
int wr_iot_http_is_post(void){return post;}
const char *wr_iot_http_content_type(void){return mime;}
int wr_iot_rc_submit(const struct wr_iot_request *request,char id[33]){
 assert(request->enabled&&!strcmp(request->ssid,"IoT")&&
        !strcmp(request->password,"password123"));
 calls++;strcpy(id,"0123456789abcdef0123456789abcdef");return submit_result;
}
int wr_iot_rc_submit_config(const struct wr_iot_saved_config *config,char id[33]){
 assert(!config->profile.enabled&&!strcmp(config->profile.ssid,"IoT")&&
        !strcmp(config->profile.password,"password123"));
 config_calls++;strcpy(id,"0123456789abcdef0123456789abcdef");return submit_result;
}
int wr_iot_rc_submit_save(const struct wr_iot_saved_config *config,int explicit_save,char id[33]){
 assert(!config->profile.enabled&&!strcmp(config->profile.ssid,"IoT")&&!strcmp(config->profile.password,"password123"));
 save_calls++;save_mode=explicit_save;strcpy(id,"0123456789abcdef0123456789abcdef");return submit_result;
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
 input(body,(int)strlen(body));
 wr_iot_http_session_reset();
 assert(!wr_iot_http_csrf[0]&&!wr_iot_http_length&&!wr_iot_http_body[0]);
 output();assert(calls==1&&strstr(reply,"invalid_request"));
 strcpy(wr_iot_http_csrf,"0123456789abcdef0123456789abcdef");
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
 {char disabled[1024];const char *minimal="wr_iot_request_enable=0&token=0123456789abcdef0123456789abcdef";
  strcpy(disabled,body);strchr(disabled,'=')[1]='0';safe=1;post=1;submit_result=1;
  strcpy(wr_iot_http_csrf,"0123456789abcdef0123456789abcdef");
  input(disabled,(int)strlen(disabled));wr_iot_http_config_output("wr_iot_config.cgi",NULL);
  assert(config_calls==1&&strstr(reply,"\"accepted\":true")&&!strstr(reply,"password123"));
  assert(!strstr(reply,"applied")&&!strstr(reply,"stored_in_ram"));
  wr_iot_http_config_output("wr_iot_config.cgi",NULL);assert(config_calls==1&&strstr(reply,"invalid_request"));
  input(minimal,(int)strlen(minimal));wr_iot_http_config_output("wr_iot_config.cgi",NULL);assert(config_calls==1);
  safe=0;input(disabled,(int)strlen(disabled));wr_iot_http_config_output("wr_iot_config.cgi",NULL);assert(config_calls==1);safe=1;
  post=0;input(disabled,(int)strlen(disabled));wr_iot_http_config_output("wr_iot_config.cgi",NULL);assert(config_calls==1);post=1;
  wr_iot_http_csrf[0]='f';input(disabled,(int)strlen(disabled));wr_iot_http_config_output("wr_iot_config.cgi",NULL);assert(config_calls==1);wr_iot_http_csrf[0]='0';
  mime="application/json";input(disabled,(int)strlen(disabled));wr_iot_http_config_output("wr_iot_config.cgi",NULL);assert(config_calls==1);mime="application/x-www-form-urlencoded";
  for(int explicit_save=0;explicit_save<=1;explicit_save++){
   int before=save_calls;
   input(disabled,(int)strlen(disabled));
   if(explicit_save)wr_iot_http_save_explicit_output("wr_iot_save.cgi",NULL);
   else wr_iot_http_save_auto_output("wr_iot_save_auto.cgi",NULL);
   assert(save_calls==before+1&&save_mode==explicit_save&&strstr(reply,"accepted")&&!strstr(reply,"saved_in_flash"));
   wr_iot_http_save_auto_output("wr_iot_save_auto.cgi",NULL);assert(save_calls==before+1);
   safe=0;input(disabled,(int)strlen(disabled));wr_iot_http_save_explicit_output("",NULL);assert(save_calls==before+1);safe=1;
   post=0;input(disabled,(int)strlen(disabled));wr_iot_http_save_auto_output("",NULL);assert(save_calls==before+1);post=1;
   wr_iot_http_csrf[0]='f';input(disabled,(int)strlen(disabled));wr_iot_http_save_explicit_output("",NULL);assert(save_calls==before+1);wr_iot_http_csrf[0]='0';
   input(minimal,(int)strlen(minimal));wr_iot_http_save_explicit_output("",NULL);assert(save_calls==before+1);
  }
  requested_id="0123456789abcdef0123456789abcdef";result_observed=145;status_available=1;
  result_state=WR_IOT_RESULT_SAVED_FLASH;wr_iot_http_result_output("wr_iot_result.cgi",NULL);assert(strstr(reply,"saved_in_flash"));
  result_state=WR_IOT_RESULT_STORED_RAM;wr_iot_http_result_output("wr_iot_result.cgi",NULL);
  assert(strstr(reply,"stored_in_ram")&&!strstr(reply,"applied"));
 }
 {
  const char *view_body="token=0123456789abcdef0123456789abcdef";
  const char *duplicate="token=0123456789abcdef0123456789abcdef&token=0123456789abcdef0123456789abcdef";
  strcpy(wr_iot_http_csrf,"0123456789abcdef0123456789abcdef");safe=post=1;mime="application/x-www-form-urlencoded";
  input(view_body,(int)strlen(view_body));wr_iot_http_view_output("wr_iot_view.cgi",NULL);
  assert(view_calls==1&&strstr(reply,"\"configured\":true")&&strstr(reply,"\"enabled\":false"));
  assert(strstr(reply,"\\u003c")&&strstr(reply,"\\u003e")&&strstr(reply,"\\u0026")&&!strstr(reply,"</script>")&&!strstr(reply,"password123"));
  assert(!strstr(reply,"\"password\"")&&!strstr(reply,"psk")&&!wr_iot_http_length&&!wr_iot_http_body[0]);
  wr_iot_http_view_output("",NULL);assert(view_calls==1&&strstr(reply,"invalid_request"));
  safe=0;input(view_body,(int)strlen(view_body));wr_iot_http_view_output("",NULL);assert(view_calls==1);safe=1;
  post=0;input(view_body,(int)strlen(view_body));wr_iot_http_view_output("",NULL);assert(view_calls==1);post=1;
  mime="application/json";input(view_body,(int)strlen(view_body));wr_iot_http_view_output("",NULL);assert(view_calls==1);mime="application/x-www-form-urlencoded";
  wr_iot_http_csrf[0]='f';input(view_body,(int)strlen(view_body));wr_iot_http_view_output("",NULL);assert(view_calls==1);wr_iot_http_csrf[0]='0';
  input(view_body,(int)strlen(view_body)-1);wr_iot_http_view_output("",NULL);assert(view_calls==1);
  input(duplicate,(int)strlen(duplicate));wr_iot_http_view_output("",NULL);assert(view_calls==1);
  for(int answer=0;answer<=3;answer++){
   int before=view_calls;view_reply=answer;
   input(view_body,(int)strlen(view_body));wr_iot_http_view_output("",NULL);
   assert(view_calls==before+1&&!wr_iot_http_length&&!wr_iot_http_body[0]);
   if(answer==0||answer==3)assert(strstr(reply,"unavailable_or_busy")&&!strstr(reply,"revision"));
   if(answer==2)assert(strstr(reply,"\"configured\":false")&&strstr(reply,"\"key_present\":false")&&strstr(reply,"\"ssid\":\"\""));
  }
 }
 {
  const char *edit="wr_iot_request_enable=0&wr_iot_request_ssid=IoT&wr_iot_request_psk=&wr_iot_request_gateway=192.168.50.1&wr_iot_request_mask=255.255.255.0&wr_iot_request_start=192.168.50.20&wr_iot_request_end=192.168.50.200&token=0123456789abcdef0123456789abcdef&revision=ffffffffffffffffffffffffffffffff&key_action=keep";
  void (*handlers[])(const char *,FILE *)={wr_iot_http_edit_ram_output,wr_iot_http_edit_auto_output,wr_iot_http_edit_save_output};
  for(int mode=0;mode<3;mode++){
   int before=edit_calls;submit_result=1;
   input(edit,(int)strlen(edit));handlers[mode]("",NULL);
   assert(edit_calls==before+1&&edit_mode==(enum wr_iot_config_edit_mode)mode&&strstr(reply,"accepted")&&!strstr(reply,"password")&&!strstr(reply,"revision"));
   handlers[mode]("",NULL);assert(edit_calls==before+1&&strstr(reply,"invalid_request"));
   safe=0;input(edit,(int)strlen(edit));handlers[mode]("",NULL);assert(edit_calls==before+1);safe=1;
   post=0;input(edit,(int)strlen(edit));handlers[mode]("",NULL);assert(edit_calls==before+1);post=1;
   wr_iot_http_csrf[0]='f';input(edit,(int)strlen(edit));handlers[mode]("",NULL);assert(edit_calls==before+1);wr_iot_http_csrf[0]='0';
   submit_result=0;input(edit,(int)strlen(edit));handlers[mode]("",NULL);
   assert(edit_calls==before+2&&strstr(reply,"unavailable_or_busy")&&!wr_iot_http_length&&!wr_iot_http_body[0]);
  }
 }
 puts("PASS IoT CGI: runtime/config/Save/view preserved, three guarded edit POST routes with endpoint-owned modes, one-shot body, CSRF and queue-only results; native/IPC actors");
 return 0;
}
