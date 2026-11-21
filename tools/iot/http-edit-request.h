#ifndef WR_IOT_HTTP_EDIT_REQUEST_H
#define WR_IOT_HTTP_EDIT_REQUEST_H
#include "http-form.h"
#include "config-edit-record.h"
static inline int wr_iot_http_edit_request_read(struct wr_iot_config_edit_record *out,
 int authenticated,const char *method,const char *content_type,const char *expected_token,
 const char *body,size_t length,enum wr_iot_config_edit_mode mode)
{
 static const char *names[]={"wr_iot_request_enable","wr_iot_request_ssid","wr_iot_request_psk",
  "wr_iot_request_gateway","wr_iot_request_mask","wr_iot_request_start","wr_iot_request_end",
  "token","revision","key_action"};
 struct wr_iot_config_edit_record candidate={0};char enabled[2]={0},token[33]={0},action[8]={0};
 char *values[]={enabled,candidate.fields.profile.ssid,candidate.fields.profile.password,
  candidate.fields.profile.gateway,candidate.fields.profile.mask,candidate.fields.profile.first,
  candidate.fields.profile.last,token,candidate.revision,action};
 const size_t capacities[]={2,33,65,16,16,16,16,33,33,8};
 unsigned int present=0,difference=0;size_t start,end,equal,index;int match,ok=0;
 if(!out||authenticated!=1||!method||strcmp(method,"POST")||!content_type||
    strcmp(content_type,"application/x-www-form-urlencoded")||!wr_iot_control_id(expected_token)||
    !body||!length||length>WR_IOT_HTTP_FORM_MAX||mode<WR_IOT_EDIT_RAM||mode>WR_IOT_EDIT_RUNTIME)goto done;
 for(start=0;start<length;start=end+1){
  for(end=start;end<length&&body[end]!='&';end++)if(!body[end])goto done;
  if(end==start)goto done;
  for(equal=start;equal<end&&body[equal]!='=';equal++);
  if(equal==start||equal==end)goto done;
  match=-1;
  for(index=0;index<10;index++)if(strlen(names[index])==equal-start&&!memcmp(body+start,names[index],equal-start)){match=(int)index;break;}
  if(match<0||(present&(1U<<match))||
     !wr_iot_http_value(values[match],capacities[match],body+equal+1,end-equal-1))goto done;
  present|=1U<<match;
  if(end==length)break;
  if(end+1==length)goto done;
 }
 if(present!=1023||!wr_iot_control_id(token)||!wr_iot_control_id(candidate.revision))goto done;
 for(index=0;index<32;index++)difference|=(unsigned char)expected_token[index]^(unsigned char)token[index];
 if(difference)goto done;
 if(!strcmp(enabled,"0"))candidate.fields.profile.enabled=0;
 else if(!strcmp(enabled,"1"))candidate.fields.profile.enabled=1;
 else goto done;
 if(!strcmp(action,"keep"))candidate.action=WR_IOT_CONFIG_KEY_KEEP;
 else if(!strcmp(action,"replace"))candidate.action=WR_IOT_CONFIG_KEY_REPLACE;
 else goto done;
 memset(candidate.id,'0',32);candidate.created=1;candidate.mode=mode;
 if(!wr_iot_config_edit_record_valid(&candidate))goto done;
 memset(candidate.id,0,sizeof(candidate.id));candidate.created=0;*out=candidate;ok=1;
 done:wr_iot_saved_wipe(&candidate,sizeof(candidate));wr_iot_saved_wipe(token,sizeof(token));
 wr_iot_saved_wipe(action,sizeof(action));wr_iot_saved_wipe(enabled,sizeof(enabled));return ok;
}
#endif
