#include "http-edit-request.h"
#include <assert.h>
#include <stdio.h>
int main(void)
{
 const char *token="0123456789abcdef0123456789abcdef";
 const char *body="wr_iot_request_enable=0&wr_iot_request_ssid=IoT%20%3C%26&wr_iot_request_psk=&wr_iot_request_gateway=192.168.50.1&wr_iot_request_mask=255.255.255.0&wr_iot_request_start=192.168.50.20&wr_iot_request_end=192.168.50.200&token=0123456789abcdef0123456789abcdef&revision=ffffffffffffffffffffffffffffffff&key_action=keep";
 struct wr_iot_config_edit_record output,before;char changed[1024];
 for(int mode=0;mode<3;mode++){
  assert(wr_iot_http_edit_request_read(&output,1,"POST","application/x-www-form-urlencoded",token,body,strlen(body),mode));
  assert(output.mode==(enum wr_iot_config_edit_mode)mode&&output.action==WR_IOT_CONFIG_KEY_KEEP&&
         !output.created&&!output.id[0]&&!output.fields.profile.password[0]&&!strcmp(output.fields.profile.ssid,"IoT <&"));
 }
 memset(&output,0x5a,sizeof(output));before=output;
 for(size_t length=0;length<strlen(body);length++){
  assert(!wr_iot_http_edit_request_read(&output,1,"POST","application/x-www-form-urlencoded",token,body,length,0));
  assert(!memcmp(&output,&before,sizeof(output)));
 }
 const char *suffixes[]={"&token=x","&mode=explicit","&unknown=x","&"};
 for(size_t index=0;index<4;index++){
  snprintf(changed,sizeof(changed),"%s%s",body,suffixes[index]);
  assert(!wr_iot_http_edit_request_read(&output,1,"POST","application/x-www-form-urlencoded",token,changed,strlen(changed),0));
 }
 strcpy(changed,body);char *action=strstr(changed,"key_action=keep");strcpy(action,"key_action=replace");
 assert(!wr_iot_http_edit_request_read(&output,1,"POST","application/x-www-form-urlencoded",token,changed,strlen(changed),0));
 assert(!wr_iot_http_edit_request_read(&output,0,"POST","application/x-www-form-urlencoded",token,body,strlen(body),0));
 assert(!wr_iot_http_edit_request_read(&output,1,"GET","application/x-www-form-urlencoded",token,body,strlen(body),0));
 assert(!wr_iot_http_edit_request_read(&output,1,"POST","application/json",token,body,strlen(body),0));
 assert(!wr_iot_http_edit_request_read(&output,1,"POST","application/x-www-form-urlencoded","ffffffffffffffffffffffffffffffff",body,strlen(body),0));
 assert(!memcmp(&output,&before,sizeof(output)));
 puts("PASS edit POST parser: exact complete fields, KEEP without key, endpoint-owned mode, no caller transaction identity, auth/CSRF/duplicate/truncation/unknown-field refusal; no HTTP binding");return 0;
}
